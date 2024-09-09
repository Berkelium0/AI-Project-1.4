# Repository for ss24.1.4/team765

This is the repository for you solution. You can modify this README file any way you see fit.

**Topic:** SS24 Assignment 1.4: Query Math Data

# Problem Solver with Blazegraph Integration

## Dependencies

- **Python 3.11**  
  Ensure you have Python 3.11 installed on your system. You can download it
  from [Python's official site](https://www.python.org/downloads/).

- **Blazegraph Server**  
  The code interacts with a Blazegraph server that hosts the dataset. Set up a Blazegraph server with your dataset
  before running the scripts. You can find Blazegraph [here](https://github.com/blazegraph/database).

- **External Libraries**
  The required Python libraries are:
    - xml.sax
    - rdflib (for URIRef, Literal, Namespace, RDF)
    - time
    - requests
    - xml.etree.ElementTree
    - urllib.parse

## How to Run the Code

1. Set up the Blazegraph server with the appropriate dataset.
2. Modify the file names in the script(s) to match your dataset or input files.
3. Execute the scripts in your Python environment.

## Repository Structure

- **Examples/**: Contains example questions along with corresponding solutions.
- **Problems_and_Solutions/**: Stores solutions to the real-world problems.
- **problem_solver.py**: This script takes problem definitions in XML, sends queries to BlazeGraph, and processes the
  returned data. It reformats and writes the answers.
- **splitter.py**: A utility script used for splitting large datasets into smaller parts for easier processing and
  uploading.
- **upload_rdf.sh**: Shell script for uploading split and formatted RDF datasets to BlazeGraph.
- **xml_to_rdf.py**: A script for converting XML files to RDF format.

## Solution Summary

### Step 1: From XML to RDF Conversion

In the first step, the goal was to convert the provided XML dataset into RDF format. I initially developed
the `xml_to_rdf.py` script for this task.

#### Mini Dataset Conversion

For the smaller mini dataset, the conversion process was straightforward. The file size was manageable, allowing me to
convert it to a Turtle structure in one go without any performance issues. The script ensured that attributes with
multiple entries—such as `classification`, `author_id`, and `keyword`—were correctly handled, adding all relevant values
with the appropriate RDF prefix.

#### Large Dataset Conversion

However, when working with the larger dataset, the memory usage became an issue. At one point, I observed my system
using over 70GB of memory on a laptop with only 16GB of physical memory, forcing me to stop the process to prevent
potential damage.

To address this issue, I created a helper script called `splitter.py`. This script splits large RDF files into smaller,
manageable chunks of around 500MB each. By processing these smaller chunks, I was able to efficiently convert the larger
dataset into RDF without overwhelming system resources.

---

### Code Overview

Brief explanation of the `xml_to_rdf.py` script:

- **Namespaces**: Defined two RDF namespaces: `ZBMATH` and `ZBMATH2`. These are used to reference elements from the XML
  data.

- **SAX Parser**: I used Python's `xml.sax` parser, which is a memory-efficient approach for handling large XML files by
  processing them incrementally.

- **Buffering and Chunking**:
    - The handler reads XML records one by one, collecting multiple attributes such as `authors`, `classifications`,
      and `keywords`.
    - It stores triples (RDF statements) in a buffer until the buffer exceeds a certain size (e.g., 1MB), at which point
      it writes the buffer to the RDF output file.
    - This chunking approach helps avoid memory overuse by flushing data in smaller portions.

- **Triple Serialization**: RDF triples are generated for each record and serialized into Turtle format, ready for
  writing to the output file.

Brief overview of the `splitter.py` script:

- **Splitting Large Files**: The script takes an RDF file and splits it into smaller chunks. The maximum chunk size is
  determined by the user (e.g., 500MB).
- **File Writing**: Once the chunk size exceeds the specified limit, a new part file is created, allowing for more
  manageable RDF uploads to BlazeGraph.

By using both scripts, I was able to convert large XML datasets into RDF in a way that is both memory-efficient and
scalable for big data sets.

### Step 2: Importing the Files to Blazegraph

After converting the datasets to RDF, the next step was to upload them to Blazegraph. Setting up Blazegraph itself was
straightforward. I created two namespaces—one for the mini dataset and another for the larger dataset.

#### Mini Dataset

For the mini dataset, uploading was simple. Using Blazegraph's built-in graphical user interface (GUI), I could upload
the file directly without any issues.

#### Large Dataset

However, the large dataset posed a challenge. The size of the files was too big to upload via the GUI. Instead of
manually specifying the file paths for each RDF part file, I wrote a Bash script named `upload_rdf.sh` to automate this
process. This script loops through all the RDF part files and uploads them to the Blazegraph SPARQL endpoint.

---

### Bash Script Summary: `upload_rdf.sh`

Brief overview of the `upload_rdf.sh` script:

- **Variables**:
    - `SPARQL_ENDPOINT`: The URL of the Blazegraph SPARQL endpoint where the data is uploaded.
    - `CONTENT_TYPE`: Specifies the type of content being uploaded (in this case, `n-triples` format).
    - `PARTS_DIR`: The directory path where all the split RDF files are stored.

- **File Upload Loop**:
    - The script loops through each RDF part file (`*.part*`) in the specified directory.
    - For each file, it uses `curl` to send a POST request to the SPARQL endpoint, uploading the file.
    - After each file is uploaded, a message confirms its successful upload.

  ### Step 3: From Problems to Solutions

The final step in the process involved solving the problems provided in the XML file. The task was to convert each
problem into a valid SPARQL query, send it to Blazegraph, retrieve the results, and reformat them in the desired output
format.

#### Querying Process Overview

1. **Problem Parsing**:
    - The problems were stored in an XML file. My code loaded and parsed this XML file to extract individual problem
      elements.

2. **SPARQL Query Generation**:
    - For each problem, depending on its type (e.g., keyword-based, MSC-intersection, top authors), a corresponding
      SPARQL query was dynamically generated. Some of these queries were simple, while others (like the classification
      intersection queries) required complex filtering to extract results from the dataset.

3. **Query Execution**:
    - These SPARQL queries were sent to Blazegraph using an HTTP POST request. The code handled the interaction with
      Blazegraph's SPARQL endpoint, where the query was processed and results were returned in XML format.

4. **Reformatting the Response**:
    - The responses received from Blazegraph were parsed, and the relevant data (keywords, documents, authors, etc.) was
      extracted. The data was then reformatted into a specific XML structure for solutions.

5. **Performance Considerations**:
    - For the mini dataset, this entire process was quick and efficient. However, when dealing with the big dataset,
      certain queries, particularly those involving classification, required significant CPU processing power. At one
      point, my laptop’s CPU reached 110°C, forcing me to use a ventilator to cool it down during execution. Despite the
      heavy load, the queries ultimately returned correct results after some time.

---

### Python Code Summary

Here’s a high-level explanation of my Python code:

- **XML Parsing**:
    - The code begins by parsing the XML file containing the problems using Python's `xml.etree.ElementTree` library.

- **SPARQL Query Generation**:
    - There are several functions that handle the generation of specific SPARQL queries depending on the type of
      problem:
        - `generate_top_authors_query`: Creates a query to retrieve the top authors based on keyword usage and
          publication years.
        - `generate_sparql_query`: This function detects the type of problem (e.g., keyword, classification
          intersection, top authors) and constructs the appropriate SPARQL query for Blazegraph.

- **Query Execution**:
    - The `send_sparql_query` function sends the generated query to the Blazegraph SPARQL endpoint using an HTTP POST
      request via the `requests` library. The query results are returned in SPARQL XML format.

- **Solution Formatting**:
    - The `format_solution` function interprets the SPARQL query results and reformats them into the correct XML
      structure for solutions, handling different types of results like keywords, document URIs, and authors.
    - The `write_solutions_to_xml` function takes all the formatted solutions and writes them to an XML file.

- **Response Handling**:
    - Depending on the problem type, the response is processed to extract keywords, classification codes, document URIs,
      and author IDs. These extracted elements are then formatted into the solution XML.

---

### Example Queries

Here are the example queries for each problem type that were used to interact with the Blazegraph SPARQL endpoint:

#### 1. **Keyword Query Example**

This query retrieves distinct keywords for a given author (in this case, the author ID is `leung.debbie-w`).

```sparql
PREFIX ns1: <http://zbmath.org/zbmath/elements/1.0/zbmath:>
SELECT DISTINCT ?keyword
WHERE {
    ?document ns1:author_id "leung.debbie-w" .
    ?document ns1:keyword ?keyword .
}
```

#### 2. **MSC Intersection Query Example**

This query identifies documents classified under three MSC (Mathematics Subject Classification) codes: `00A71`, `00B25`,
and `93-06`.

```sparql
PREFIX ns1: <http://zbmath.org/zbmath/elements/1.0/zbmath:>
SELECT DISTINCT ?document
WHERE {
    ?document ns1:classification ?class1 .
    ?document ns1:classification ?class2 .
    ?document ns1:classification ?class3 .
    FILTER (STRSTARTS(STR(?class1), "00A71") && STRSTARTS(STR(?class2), "00B25") &&
    STRSTARTS(STR(?class3), "93-06"))
}
ORDER BY ?document
```

#### 3. **Top Authors Query Example**

This query finds the top 10 authors who have published works related to the keyword "Fourier transforms" between 1977
and 2013, ordered by the number of distinct documents they have authored.

```sparql
PREFIX ns1: <http://zbmath.org/zbmath/elements/1.0/zbmath:>
SELECT DISTINCT ?author_id (COUNT(DISTINCT ?document) AS ?count)
WHERE {
    ?document ns1:keyword "Fourier transforms" .
    ?document ns1:author_id ?author_id .
    ?document ns1:publication_year ?publication_year .
    FILTER(?publication_year > "1977" && ?publication_year < "2013")  # Exclude limiting years
}
GROUP BY ?author_id
ORDER BY DESC(?count)
LIMIT 10
```


---

In conclusion, the code successfully parsed the problems, generated appropriate SPARQL queries, interacted with
Blazegraph, and produced formatted solutions despite the challenges posed by the large dataset's complexity and size.