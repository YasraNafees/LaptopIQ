"""
testing.py - LaptopIQ Pipeline Test Suite
==========================================
This file contains the testing structure for the LaptopIQ RAG pipeline.

Tests are organized in 3 sections:
    1. Basic pipeline tests   - imports, index, chat engine
    2. Manual query tests     - real query validation
    3. RAGAS evaluation       - faithfulness, relevancy, recall scoring

NOTE:
    Full RAGAS evaluation is run separately in a Colab environment
    due to compute requirements. This file handles local pipeline
    validation only.

RUN:
    python testing.py --basic     # basic pipeline checks
    python testing.py --manual    # manual query tests
    python testing.py --all       # run all local tests
"""

import argparse
import sys
import traceback


# ============================================================
# SECTION 1: BASIC PIPELINE TESTS
# ============================================================

def test_imports():
    """Verify all required modules load correctly."""
    print("\n[TEST] Import check...")
    try:
        from creating_vectordatabase import build_vector_database
        from Reterival_engine import create_chat_engine
        print("  PASS - All imports successful")
        return True
    except ImportError as e:
        print(f"  FAIL - {e}")
        return False


def test_index_build():
    """Verify index builds or loads from disk correctly."""
    print("\n[TEST] Index build/load check...")
    try:
        from creating_vectordatabase import build_vector_database
        index, nodes = build_vector_database(force_rebuild=False)

        assert index is not None, "Index returned None"
        assert nodes is not None, "Nodes returned None"
        assert len(nodes) > 0, f"Empty nodes: {len(nodes)}"

        print(f"  PASS - Index loaded. Nodes: {len(nodes)}")
        return index, nodes
    except Exception as e:
        print(f"  FAIL - {e}")
        traceback.print_exc()
        return None, None


def test_chat_engine(index, nodes):
    """Verify chat engine initializes correctly."""
    print("\n[TEST] Chat engine check...")
    try:
        from Reterival_engine import create_chat_engine
        chat_engine = create_chat_engine(index, nodes)

        assert chat_engine is not None, "Chat engine returned None"
        print("  PASS - Chat engine created")
        return chat_engine
    except Exception as e:
        print(f"  FAIL - {e}")
        traceback.print_exc()
        return None


def test_single_response(chat_engine):
    """Verify pipeline returns a non-empty response."""
    print("\n[TEST] Single response check...")
    try:
        response = str(chat_engine.chat("Show me Asus laptops")).strip()

        assert len(response) > 0, "Empty response"
        assert response != "None", "Response is None string"

        print(f"  PASS - Response received ({len(response)} chars)")
        print(f"  Preview: {response[:150]}...")
        return True
    except Exception as e:
        print(f"  FAIL - {e}")
        traceback.print_exc()
        return False


def run_basic_tests():
    print("\n" + "=" * 50)
    print("SECTION 1: BASIC PIPELINE TESTS")
    print("=" * 50)

    results = {}

    results["imports"] = test_imports()
    if not results["imports"]:
        print("\nImports failed. Fix before running further tests.")
        return results, None, None

    index, nodes = test_index_build()
    results["index"] = index is not None
    if not results["index"]:
        print("\nIndex failed. Fix before running further tests.")
        return results, None, None

    chat_engine = test_chat_engine(index, nodes)
    results["chat_engine"] = chat_engine is not None

    if results["chat_engine"]:
        results["single_response"] = test_single_response(chat_engine)

    passed = sum(1 for v in results.values() if v)
    print(f"\nResult: {passed}/{len(results)} passed")
    return results, index, nodes


# ============================================================
# SECTION 2: MANUAL QUERY TESTS
# Update these queries to match your actual CSV data
# ============================================================

MANUAL_TEST_QUERIES = [
    {
        "query": "Show me Asus laptops under $1200",
        "must_contain": ["Asus"],
        "must_not_contain": [],
    },
    {
        "query": "What is the cheapest laptop available?",
        "must_contain": ["$"],
        "must_not_contain": [],
    },
    {
        "query": "I need a gaming laptop with 16GB RAM",
        "must_contain": ["GB"],
        "must_not_contain": [],
    },
    {
        "query": "Do you have a laptop with 128GB RAM?",
        "must_contain": [],
        "must_not_contain": [],
    },
    {
        "query": "asdkjasd random input 123",
        "must_contain": [],
        "must_not_contain": [],
    },
]


def run_manual_tests(index, nodes):
    print("\n" + "=" * 50)
    print("SECTION 2: MANUAL QUERY TESTS")
    print("=" * 50)

    from Reterival_engine import create_chat_engine
    results = []

    for i, test in enumerate(MANUAL_TEST_QUERIES, 1):
        print(f"\n[{i}/{len(MANUAL_TEST_QUERIES)}] {test['query']}")
        try:
            engine = create_chat_engine(index, nodes)
            response = str(engine.chat(test["query"])).strip()

            passed = True
            fail_reasons = []

            for word in test["must_contain"]:
                if word.lower() not in response.lower():
                    passed = False
                    fail_reasons.append(f"Expected '{word}' not found in response")

            for word in test["must_not_contain"]:
                if word.lower() in response.lower():
                    passed = False
                    fail_reasons.append(f"Unexpected '{word}' found in response")

            print(f"  {'PASS' if passed else 'FAIL'}")
            print(f"  Response: {response[:200]}...")
            for r in fail_reasons:
                print(f"  REASON: {r}")

            results.append(passed)

        except Exception as e:
            print(f"  FAIL - {e}")
            results.append(False)

    print(f"\nResult: {sum(results)}/{len(results)} passed")
    return results


# ============================================================
# SECTION 3: RAGAS EVALUATION
# Full RAGAS eval runs in Colab - see /colab/ragas_eval.ipynb
# ============================================================

def run_ragas_eval():
    print("\n" + "=" * 50)
    print("SECTION 3: RAGAS EVALUATION")
    print("=" * 50)
    print("Full RAGAS evaluation is handled in the Colab environment.")
    print("See: colab/ragas_eval.ipynb")
    print("\nMetrics evaluated:")
    print("  - Faithfulness              (hallucination detection)")
    print("  - Response Relevancy        (answer quality)")
    print("  - Context Precision         (retriever accuracy)")
    print("  - Context Recall            (retriever coverage)")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="LaptopIQ Test Suite")
    parser.add_argument("--basic", action="store_true")
    parser.add_argument("--manual", action="store_true")
    parser.add_argument("--ragas", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if not any([args.basic, args.manual, args.ragas, args.all]):
        args.basic = True

    index, nodes = None, None

    if args.basic or args.all:
        results, index, nodes = run_basic_tests()
        if not all(results.values()):
            print("\nBasic tests failed. Stopping.")
            sys.exit(1)

    if (args.manual or args.all) and index is None:
        from creating_vectordatabase import build_vector_database
        index, nodes = build_vector_database(force_rebuild=False)

    if args.manual or args.all:
        run_manual_tests(index, nodes)

    if args.ragas or args.all:
        run_ragas_eval()

    print("\n" + "=" * 50)
    print("Done.")
    print("=" * 50)


if __name__ == "__main__":
    main()