from datasources.faiss_ds import FAISSDS
from utils.formatter import subject_code_from_subject_name


def search_datasource(datasource_name, query, top_k=5):
    """
    Search the datasource and return the top_k results.
    """
    try:
        # Initialize the FAISSDS object with the datasource name
        faiss_ds = FAISSDS(index_name=datasource_name)

        # Perform the search
        results = faiss_ds.search_request(search_query=query, topk=top_k)

        # Return the results
        return results
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


if __name__ == "__main__":
    # Example usage
    datasource_name = "Project Management"  # Replace with your datasource name

    # Search example
    query = "what is the typical project management life cycle?"  # Replace with your search query
    top_k = 5  # Number of top results to retrieve

    print("Performing search...")
    # format the datasource_name into subject code
    datasource_name = subject_code_from_subject_name(datasource_name)
    search_results = search_datasource(datasource_name, query, top_k)

    # Print search results
    for i, result in enumerate(search_results, start=1):
        print(f"Result {i}:")
        print(f"ID: {result['id']}")
        print(f"Content: {result['content']}")
        print(f"File URL: {result['file_url']}")
        print(f"Score: {result['score']}")
        print("-" * 50)
