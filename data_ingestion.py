import sys
import hashlib
import pandas as pd
from llama_index.core import Document
from config import Config
from logger import logger


def generate_doc_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_and_clean_data(csv_path: str) -> list:
    logger.info(f"Loading data from: {csv_path}")
    print(f" Loading CSV: {csv_path}")
    
    df = pd.read_csv(csv_path).drop_duplicates()
    print(f" Found {len(df)} rows in CSV")
    
    # Column detection
    company_col = next(
        (c for c in df.columns if "brand" in c.lower() or "company" in c.lower()),
        df.columns[0] if len(df.columns) > 0 else None
    )
    
    product_col = next(
        (c for c in df.columns if "product" in c.lower() or "model" in c.lower()),
        df.columns[1] if len(df.columns) > 1 else None
    )
    
    cpu_col = next(
        (c for c in df.columns if "cpu" in c.lower() or "processor" in c.lower()),
        df.columns[2] if len(df.columns) > 2 else None
    )
    
    price_col = next(
        (c for c in df.columns if "price" in c.lower()),
        None
    )
    
    ram_col = next(
        (c for c in df.columns if "ram" in c.lower()),
        None
    )
    
    print(f" Columns - Brand: {company_col}, Product: {product_col}, Price: {price_col}")
    
    documents = []
    seen_texts = set()  # ✅ Deduplication

    for idx, row in df.iterrows():
        brand = str(row.get(company_col, "Unknown")).strip()
        product = str(row.get(product_col, "Unknown")).strip()
        cpu = str(row.get(cpu_col, "Unknown")).strip()
        ram = row.get(ram_col, "N/A")
        
        # ✅ FIXED: Price ko round karo
        raw_price = row.get(price_col, 0)
        try:
            price = round(float(raw_price), 2)  # ✅ Round to 2 decimals
        except:
            price = 0.0
        
        # ✅ Clean RAM value
        try:
            ram_clean = str(int(float(str(ram).replace('GB', '').strip())))
        except:
            ram_clean = str(ram)
        
        text = f"Brand: {brand}. Model: {product}. CPU: {cpu}. RAM: {ram_clean}GB. Price: ${price}"

        # ✅ Skip duplicates
        if text in seen_texts:
            continue
        seen_texts.add(text)

        doc_id = generate_doc_hash(text)

        doc = Document(
            text=text,
            doc_id=doc_id,
            metadata={
                "brand": brand,
                "product": product,  # ✅ Add product for better tracking
                "price": price,
            },
        )

        documents.append(doc)

    print(f"Created {len(documents)} unique documents")
    return documents


def main():
    try:
        logger.info("Starting Ingestion Process")
        documents = load_and_clean_data(Config.CSV_PATH)
        logger.info(f"Documents Created: {len(documents)}")
        print(f"Ingestion complete: {len(documents)} documents")

    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        print(f" Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()