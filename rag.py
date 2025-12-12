### Block 2: Import thư viện
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
### Block 3: Load dataset từ Hugging Face
dataset = load_dataset("synguyen1106/vietnam_heritage_embeddings_v2", split="train")

# Chuyển vector embeddings sang numpy float32
vectors = np.array(dataset['embedding']).astype("float32")

# Tách metadata (loại bỏ id, slug, vector)
metadata = [
    {k:v for k,v in dataset[i].items() if k not in ['embedding','id','slug']}
    for i in range(len(dataset))
]
ids = [dataset[i]['id'] for i in range(len(dataset))]
print(f"Loaded {len(ids)} items from dataset.")
### Block 4: Tạo FAISS CPU index
d = vectors.shape[1]  # dimension của vector
index = faiss.IndexFlatL2(d)  # FAISS CPU
index.add(vectors)
print("Number of vectors in FAISS index:", index.ntotal)
model = SentenceTransformer("all-MiniLM-L6-v2")  # CPU, hoặc device='cuda' nếu muốn GPU
### Block 6: RAG query function
def retrieve_context(query, k=2):
    # Encode query
    query_vec = model.encode([query], convert_to_numpy=True).astype("float32")

    # Search FAISS
    distances, indices = index.search(query_vec, k)

    results = []
    for i, idx in enumerate(indices[0]):
        idx = int(idx)  # ép sang int để dataset HF nhận
        result = {
            "metadata": metadata[idx]
        }
        results.append(result)
    return results