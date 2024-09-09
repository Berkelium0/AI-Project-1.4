import xml.sax
from rdflib import URIRef, Literal, Namespace, RDF
from io import StringIO

# Define namespaces
ZBMATH = Namespace("http://zbmath.org/zbmath/elements/1.0/zbmath:")
ZBMATH2 = Namespace("http://zbmath.org/zbmath/elements/1.0/")

class ZbmathHandler(xml.sax.ContentHandler):
    def __init__(self, output_file, chunk_size=1_000_000):
        super().__init__()
        self.current_data = ""
        self.record_data = {}
        self.in_record = False
        self.authors = []  # To hold multiple authors
        self.classifications = []  # To hold multiple classifications
        self.keywords = []  # To hold multiple keywords
        self.output_file = output_file
        self.chunk_size = chunk_size  # Buffer size for writing to file (in bytes)
        self.triples_buffer = []  # Buffer to accumulate triples
        self.buffer_size = 0  # Track buffer size in bytes
        self.file = open(output_file, 'a')  # Open file in append mode

    def startElement(self, name, attrs):
        self.current_data = name
        if name == "record":
            self.in_record = True
            self.record_data = {}
            self.authors = []  # Reset for each record
            self.classifications = []  # Reset for each record
            self.keywords = []  # Reset for each record
        elif self.in_record and name.startswith("zbmath:"):
            self.record_data[name] = ""

    def endElement(self, name):
        if name == "record":
            self.in_record = False
            self.add_record_to_buffer()
            if self.buffer_size > self.chunk_size:  # Check buffer size
                self.write_buffer_to_file()
                self.triples_buffer = []  # Reset buffer
                self.buffer_size = 0  # Reset buffer size
        elif name == "zbmath:classification":  # Handle classification separately
            if self.characters.strip():  # If classification exists
                self.classifications.append(self.characters.strip())  # Add to list
        elif name == "zbmath:author_id":  # Handle author ID separately
            if self.characters.strip():  # If author ID exists
                self.authors.append(self.characters.strip())  # Add to list
        elif name == "zbmath:keyword":  # Handle keyword separately
            if self.characters.strip():  # If keyword exists
                self.keywords.append(self.characters.strip())  # Add to list
        elif self.in_record and name in self.record_data:
            self.record_data[name] = self.characters.strip()

    def characters(self, content):
        if self.current_data in self.record_data or self.current_data in ["zbmath:classification", "zbmath:author_id", "zbmath:keyword"]:
            self.characters = content.strip()  # Store characters for use in endElement

    def add_record_to_buffer(self):
        if 'zbmath:document_id' in self.record_data:
            doc_id = self.record_data['zbmath:document_id']
            subject_uri = URIRef(ZBMATH[doc_id])

            # Create triples and serialize them directly
            triples = []
            triples.append((subject_uri, RDF.type, ZBMATH.Document))

            # Add all fields except classification, author_id, and keyword
            for key, value in self.record_data.items():
                if value and key not in ['zbmath:classification', 'zbmath:author_id', 'zbmath:keyword']:
                    triples.append((subject_uri, ZBMATH2[key], Literal(value)))

            # Add multiple classifications if present
            for classification in self.classifications:
                triples.append((subject_uri, ZBMATH.classification, Literal(classification)))

            # Add multiple authors if present
            for author in self.authors:
                triples.append((subject_uri, ZBMATH.author_id, Literal(author)))

            # Add multiple keywords if present
            for keyword in self.keywords:
                triples.append((subject_uri, ZBMATH.keyword, Literal(keyword)))

            # Serialize triples and write directly to buffer
            for triple in triples:
                serialized_triple = self.serialize_triple(triple)
                self.triples_buffer.append(serialized_triple)
                self.buffer_size += len(serialized_triple)

    def serialize_triple(self, triple):
        # Serialize each triple to Turtle format
        #print(triple, f"{triple[0].n3()} {triple[1].n3()} {triple[2].n3()} .\n")
        return f"{triple[0].n3()} {triple[1].n3()} {triple[2].n3()} .\n"

    def write_buffer_to_file(self):
        self.file.writelines(self.triples_buffer)
        self.file.flush()  # Ensure data is written to disk

    def endDocument(self):
        if self.triples_buffer:
            self.write_buffer_to_file()  # Write any remaining data in buffer
        self.file.close()  # Close the file after processing

# Initialize parser
parser = xml.sax.make_parser()
handler = ZbmathHandler('big-output.rdf', chunk_size=1_000_000)  # Set buffer size (e.g., 1 MB)
parser.setContentHandler(handler)

# Parse the XML file
parser.parse("Big Dataset.xml")