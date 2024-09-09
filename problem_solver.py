import time

import requests
import xml.etree.ElementTree as ET
import urllib.parse
from urllib.parse import quote_plus

# Load and parse the XML file
file_path = 'problems-big.xml'
tree = ET.parse(file_path)
root = tree.getroot()

# SPARQL endpoint URL
sparql_endpoint = 'http://192.168.178.34:9999/bigdata/namespace/big_dataset/sparql'  # Ensure this is the correct endpoint


# Function to extract the author ID from a URI
def extract_author_id(uri):
    query_string = urllib.parse.urlparse(uri).query
    params = urllib.parse.parse_qs(query_string)
    author_param = params.get('q', [''])[0]
    author_id = urllib.parse.unquote(author_param)
    if author_id.startswith('ai:'):
        author_id = author_id[3:]
    return author_id


# Function to extract classification codes from the URI
def extract_classification_codes(uri):
    query_string = urllib.parse.urlparse(uri).query
    params = urllib.parse.parse_qs(query_string)
    classification_param = params.get('q', [''])[0]
    classification_code = urllib.parse.unquote(classification_param)
    if classification_code.startswith('cc:'):
        classification_code = classification_code[3:]  # Strip the 'cc:' part
    return classification_code


# Function to extract the keyword from a URI
def extract_keyword(uri):
    query_string = urllib.parse.urlparse(uri).query
    params = urllib.parse.parse_qs(query_string)
    keyword_param = params.get('q', [''])[0]
    keyword = urllib.parse.unquote(keyword_param)
    if keyword.startswith('ut:'):
        keyword = keyword[3:]
    return keyword


# Function to generate SPARQL query for top authors with a keyword
def generate_top_authors_query(keyword, before_year, after_year):
    return f"""
    PREFIX ns1: <http://zbmath.org/zbmath/elements/1.0/zbmath:>

    SELECT DISTINCT ?author_id (COUNT(DISTINCT ?document) AS ?count)
    WHERE {{
        ?document ns1:keyword "{keyword}" .
        ?document ns1:author_id ?author_id .
        ?document ns1:publication_year ?publication_year .
        FILTER(?publication_year > "{after_year}" && ?publication_year < "{before_year}")  # Exclude limiting years
    }}
    GROUP BY ?author_id
    ORDER BY DESC(?count)
    LIMIT 10
    """


# Function to generate a SPARQL query from a problem element
def generate_sparql_query(problem):
    problem_type = problem.attrib['type']

    if problem_type == 'keywords':
        # Extract and process the author URI
        author_uri = problem.find('Author').text
        author_id = extract_author_id(author_uri)

        return f"""
        PREFIX ns1: <http://zbmath.org/zbmath/elements/1.0/zbmath:>
        SELECT DISTINCT ?keyword
        WHERE {{
            ?document ns1:author_id "{author_id}" .
            ?document ns1:keyword ?keyword .
        }}
        """

    elif problem_type == 'msc-intersection':
        classifications = [extract_classification_codes(elem.text) for elem in problem.findall('Classification')]
        # Dynamically create the triples and filter conditions for each classification
        classification_triples = []
        class_filters = []
        for i, cls in enumerate(classifications):
            class_var = f"?class{i + 1}"
            classification_triples.append(f"?document ns1:classification {class_var} .")
            class_filters.append(f'STRSTARTS(STR({class_var}), "{cls}")')

        # Combine triples and filters
        triples_str = '\n    '.join(classification_triples)
        filters_str = ' && '.join(class_filters)
        return f"""
               PREFIX ns1: <http://zbmath.org/zbmath/elements/1.0/zbmath:>

               SELECT DISTINCT ?document
               WHERE {{
                   {triples_str}
                   FILTER ({filters_str})
               }}
               ORDER BY ?document
               """

    elif problem_type == 'top-authors':
        keyword_uri = problem.find('Keyword').text
        before_year = problem.find('BeforeYear').text
        after_year = problem.find('AfterYear').text

        # Extract the keyword from the URI
        keyword = extract_keyword(keyword_uri)

        # Generate the SPARQL query for top authors
        return generate_top_authors_query(keyword, before_year, after_year)

    else:
        return "Unknown problem type"


# Function to send SPARQL query to the endpoint
def send_sparql_query(query):
    response = requests.post(
        sparql_endpoint,
        data={'query': query},
        headers={
            'Accept': 'application/sparql-results+xml'
        }
    )

    if response.status_code == 200:
        return response
    else:
        print(f"Error: {response.status_code}")
        return None


def format_solution(xml_data, solution_id, query_text="[REDACTED]"):
    # Parse XML
    root = ET.fromstring(xml_data)
    ns = {'sparql': 'http://www.w3.org/2005/sparql-results#'}

    # Create root Solution element
    solution = ET.Element('Solution', id=str(solution_id))

    # Add Query element
    query_element = ET.SubElement(solution, 'Query')
    query_element.text = query_text

    # Check if it's a keyword-based solution (looking for <literal> keyword results)
    keyword_results = root.findall('.//sparql:result/sparql:binding[@name="keyword"]/sparql:literal', ns)
    if keyword_results:
        # Handle keyword-based solution
        for keyword_element in keyword_results:
            keyword = keyword_element.text
            # Create a Keyword element with the formatted URL
            keyword_tag = ET.SubElement(solution, 'Keyword')
            keyword_tag.text = f"https://zbmath.org/?q=ut%3A{keyword.replace(' ', '+')}"
        return solution

    # Check if it's an MSC-intersection solution (looking for <uri> document results)
    document_results = root.findall('.//sparql:result/sparql:binding[@name="document"]/sparql:uri', ns)
    if document_results:
        # Handle MSC-intersection solution
        for document_element in document_results:
            document_uri = document_element.text
            # Extract document number from URI and format it
            doc_number = document_uri.split(':')[-1]
            paper_tag = ET.SubElement(solution, 'Paper')
            paper_tag.text = f"https://zbmath.org/?q=an%3A{doc_number}"
        return solution

    # Check if it's a top-authors solution (looking for <literal> author_id and count results)
    author_results = root.findall('.//sparql:result', ns)
    if author_results:
        # Handle top-authors solution
        for result in author_results:
            author_id_element = result.find('.//sparql:binding[@name="author_id"]/sparql:literal', ns)
            count_element = result.find('.//sparql:binding[@name="count"]/sparql:literal', ns)
            if author_id_element is not None and count_element is not None:
                author_id = author_id_element.text
                count = count_element.text
                # Create an Author element with count attribute
                author_tag = ET.SubElement(solution, 'Author', count=count)
                author_tag.text = f"https://zbmath.org/authors/?q=ai%3A{author_id}"
        return solution

    # If no known patterns matched, return an empty solution (fallback)
    return solution


def write_solutions_to_xml(solutions, output_file):
    # Create root <Solutions> element
    root = ET.Element('Solutions')

    # Add each solution to the root element
    for solution in solutions:
        root.append(solution)

    # Create ElementTree and write to file
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding='unicode', xml_declaration=True)


all_solutions = []
# Iterate through each problem in the XML file, generate a SPARQL query, and send it
for problem in root.findall('Problem'):
    sparql_query = generate_sparql_query(problem)
    # encoded_query = urllib.parse.quote_plus(sparql_query)
    print(f"Query:\n{sparql_query}")

    # Request with XML format
    response = send_sparql_query(query=sparql_query)
    if response:
        time.sleep(1)  # Introduce a 1 second delay between requests
        solution = format_solution(response.text, problem.attrib["id"], sparql_query)
    all_solutions.append(solution)

write_solutions_to_xml(all_solutions, "solutions-big.xml")