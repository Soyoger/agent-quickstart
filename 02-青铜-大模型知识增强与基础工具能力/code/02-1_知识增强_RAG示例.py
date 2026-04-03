import sys
sys.path.append('../../agent-quickstart')
import faiss
import numpy as np
import requests
from openai import OpenAI
from config import base_url, api_key

# 初始化 OpenAI 客户端
client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

# --- 向量生成 (Dense Retrieval) ---
def get_embedding(text: str) -> np.ndarray:
    """使用 Qwen/Qwen3-Embedding-4B 获取文本向量"""
    response = client.embeddings.create(
        input=text,
        model="Qwen/Qwen3-Embedding-4B"
    )
    return np.array(response.data[0].embedding).astype('float32')

def ingest_data(texts: list):
    """
    第一步：数据写入阶段。
    将原始文本转换为向量并构建 FAISS 索引。
    """
    print(f"正在开始数据写入，共 {len(texts)} 条文档...")
    embeddings = np.array([get_embedding(text) for text in texts])
    dimension = embeddings.shape[1]
    
    # 创建 FAISS 索引
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    print(f"数据写入完成，索引构建成功 (维度: {dimension})")
    return index

# --- 关键词检索 (Sparse Search) ---
def sparse_search(query: str, texts: list, top_k: int = 5):
    """一个简单的关键词匹配检索 (演示 Sparse Search)"""
    query_words = set(query.lower().split())
    scores = []
    for i, text in enumerate(texts):
        # 简单计算词重叠数作为评分
        overlap = sum(1 for word in query_words if word in text.lower())
        scores.append((i, overlap))
    
    # 按重叠度排序
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    return [idx for idx, score in sorted_scores[:top_k]]

# --- RRF 融合机制 ---
def rrf_fusion(dense_rank: list, sparse_rank: list, k: int = 60):
    """Reciprocal Rank Fusion (RRF) 融合算法"""
    scores = {}
    for rank, idx in enumerate(dense_rank):
        scores[idx] = scores.get(idx, 0) + 1 / (k + rank)
    for rank, idx in enumerate(sparse_rank):
        scores[idx] = scores.get(idx, 0) + 1 / (k + rank)
    
    sorted_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return sorted_indices

# --- Reranker 重排序 ---
def rerank(query: str, documents: list):
    """使用 Qwen/Qwen3-Reranker-4B 对候选文档进行重排序"""
    if not documents:
        return []
        
    rerank_url = f"{base_url}/rerank"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "Qwen/Qwen3-Reranker-4B",
        "query": query,
        "documents": documents,
        "top_n": 3
    }
    
    try:
        response = requests.post(rerank_url, headers=headers, json=payload)
        results = response.json().get("results", [])
        reranked_docs = []
        for res in results:
            index = res["index"]
            reranked_docs.append(documents[index])
        print(f"Rerank 成功，重排序结果为: {results}")
        return reranked_docs
    except Exception as e:
        print(f"Rerank 失败: {e}")
        return documents[:3]

# --- 核心 RAG 流程 ---
def hybrid_retrieve_with_rerank(query: str, index, texts: list):
    """
    第二步：执行检索。
    结合向量检索、关键词检索、RRF 融合及 Rerank。
    """
    print(f"\n[检索中] 用户查询: {query}")
    
    # 1. 向量检索 (Dense)
    query_embedding = get_embedding(query).reshape(1, -1)
    _, I = index.search(query_embedding, 5)
    dense_indices = I[0].tolist()
    
    # 2. 关键词检索 (Sparse)
    sparse_indices = sparse_search(query, texts, 5)
    
    # 3. RRF 融合
    fused_indices = rrf_fusion(dense_indices, sparse_indices)
    candidate_docs = [texts[idx] for idx in fused_indices]
    
    # 4. Rerank 重排序
    final_docs = rerank(query, candidate_docs)
    return "\n".join(final_docs)

def run_advanced_rag(user_prompt: str, index, texts: list):
    """执行高级 RAG 对话流程"""
    print(f"\n--- 用户提问: {user_prompt} ---")
    
    # 混合检索 + Rerank
    context = hybrid_retrieve_with_rerank(user_prompt, index, texts)
    
    messages = [
        {"role": "system", "content": f"你是一个专业的 AI 助手。请根据以下提供的参考资料准确回答问题。\n\n参考资料：\n{context}"},
        {"role": "user", "content": user_prompt}
    ]
    
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=messages,
        stream=True
    )
    
    print("\n--- 大模型回答 ---")
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n-----------------")

if __name__ == "__main__":
    # 准备知识库数据
    knowledge_base_data = [
        "大语言模型（Large Language Model，简称LLM）是一种经过大量文本数据训练的人工智能模型，能够理解和生成人类语言。",
        "LangChain 是一个开源框架，旨在帮助开发者更轻松地构建基于语言模型的应用程序。它提供了模块化的组件和链式调用的思想，可以方便地整合不同的语言模型、知识库和工具。",
        "RAG（Retrieval-Augmented Generation）的工作原理分为两步：首先，从外部知识库中检索（Retrieval）与用户问题相关的信息；然后，将这些信息与原始问题一起作为上下文，增强（Augmented）并提交给大模型，以生成（Generation）更准确、更具信息量的回答。",
        "SiliconFlow 是一个 AI 模型即服务（MaaS）平台，提供包括 DeepSeek、Qwen 在内的多种主流开源模型的托管调用接口。",
        "RRF (Reciprocal Rank Fusion) 是一种简单而有效的排序融合算法，它通过计算各个排序列表中项的倒数排名之和来确定最终排名。",
        "混合检索（Hybrid Search）通常结合了基于关键词的传统检索（如 BM25）和基于向量的语义检索，以提高检索的准确性和鲁棒性。",
        "Reranker（重排序模型）在大规模检索后对初筛结果进行二次打分，通过更精细的语义分析，从候选集中挑选出最相关的文档。"
    ]

    # --- 第一步：向量数据库写入数据 ---
    faiss_index = ingest_data(knowledge_base_data)

    # --- 第二步：执行检索与对话 ---
    # 测试用例 1
    run_advanced_rag("请详细解释一下什么是混合检索，以及 RRF 是如何发挥作用的？", faiss_index, knowledge_base_data)
    
    # 测试用例 2
    run_advanced_rag("我想了解 Reranker 模型在大模型检索中的具体价值", faiss_index, knowledge_base_data)
