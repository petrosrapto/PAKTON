"""
Description:
Structural document parser implementation. Uses LLM-based parsing to extract hierarchical sections
from documents and builds a tree structure for advanced document navigation and querying.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from pydantic import BaseModel, Field
from typing import List
from langchain_unstructured import UnstructuredLoader
from langchain_community.document_loaders import TextLoader
import uuid
import tempfile
import os
import docx2txt

from Archivist.utils import PARSING_PROMPT
from Archivist.models import get_llm

from langchain_core.documents import Document

class Section(BaseModel):
    """
    Represents a single section within a document.

    Attributes:
        id (int): A unique identifier/index for the section.
        content (str): The text content of the section.
        parentSectionId (int): The identifier of the parent section, defining the hierarchical structure of the document.
    """
    id: int = Field(None, description="The unique identifier/index of the section.")
    content: str = Field(None, description="The source text of the section.")
    parentSectionId: int = Field(None, description="The identifier/index of the section that is considered parent of the current.")
    # description: str = Field(None, description="A concise explanation of section's role and significance within the document, providing context to improve search retrieval and understanding of its purpose.")

class DocumentStructure(BaseModel):
    """
    Represents the structured representation of a document.

    Attributes:
        sections (List[Section]): A list of structured sections extracted from the document.
        summary (str): A concise summary of the document's content.
    """
    sections: List[Section] = Field(None, description="The structured list of sections extracted from the document.")
    summary: str = Field(None, description="A concise summary of the document's content.")

class SectionWithMetadata(Section):
    """
    Extends the `Section` model by adding metadata.

    Attributes:
        metadata (dict): A dictionary containing additional metadata extracted from the original document (e.g., source, filename, last modified, etc.).
    """
    metadata: dict = Field(default_factory=dict, description="Metadata extracted from the original document.")

class StructuralTree:
    """
    A class to represent a structural tree that organizes document sections hierarchically.
    Supports PDF and DOCX files and returns their sections in a tree like way.
    """
    class TreeNode:
        """
        A nested class representing a tree node.
        Each node has id, content, metadata, a reference to its parent, and a list of children.
        """
        def __init__(self, id, content, parent=None, metadata=None):
            """Initialize a tree node with id, content and an optional parent and metadata."""
            self.content = content
            self.id = id
            self.parent = parent  
            self.metadata = metadata
            self.children = []
            if parent:
                parent.add_child(self)

        def add_child(self, child):
            """Add a child node to the current node."""
            self.children.append(child)

        def __repr__(self):
            """Return a pretty representation of the current node's content only (without children)."""
            return f"[Node {self.id}]\nContent: {self.content}\nMetadata: {self.metadata}\n"

        def get_tree_structure(self, level=0):
            """Return the tree structure as a string."""
            indent = "---" * level
            result = f"{indent}- {self.content}\n"
            for child in self.children:
                result += child.get_tree_structure(level + 1)  # Recursively build string
            return result
        
        def get_children_of_node(self):
            """Return all children of the node."""
            return self.children
        
        def get_parent_of_node(self):
            """Return the parent of the node (or None if it's the root)."""
            return self.parent

        def get_siblings_of_node(self):
            """Return all siblings of the node (excluding itself)."""
            if not self.parent:
                return []  # No parent means no siblings
            return [sibling for sibling in self.parent.children if sibling != self]
        
        def get_ancestors_of_node(self, withoutRoot=False):
            """
            Return a list of all ancestor nodes from parent up to the root.
            If withoutRoot is enabled, the root isnt returned
            """
            ancestors = []
            current = self.parent
            while current:
                ancestors.append(current)
                current = current.parent
            
            # Remove the last element (root) if withoutRoot is True
            if withoutRoot and ancestors:
                ancestors.pop()

            return ancestors[::-1]  # Reverse the order before returning

        def get_descendants_of_node(self):
            """
            Return a list of all descendant nodes (children, grandchildren, etc.) of the current node.
            """
            descendants = []

            def collect_descendants(node):
                for child in node.children:
                    descendants.append(child)
                    collect_descendants(child)

            collect_descendants(self)
            return descendants

    def __init__(self, full_file_path):
        """
        Initialize the StructuralTree with a given file path.
        
        Args:
        - full_file_path: Path to the document (PDF or DOCX)
        from the pdf parsing


        Attributes:
        - The root node of the tree
        - The map of ids and nodes
        """
        ext = os.path.splitext(full_file_path)[1] 
        if ext == '.docx':
            self.root, self.node_map = self.docx_to_structuralGraph(full_file_path)
        elif ext == '.pdf':
            self.root, self.node_map = self.pdf_to_structuralGraph(full_file_path)
        elif ext == '.txt':
            self.root, self.node_map = self.txt_to_structuralGraph(full_file_path)
        else:
            raise ValueError('Invalid File format given')

    def docx_to_structuralGraph(self, full_file_path):
        """
        Convert a DOCX file to a structural graph by first extracting the text content
        and then processing it using the txt_to_structuralGraph method.
        
        Args:
        - full_file_path: Path to the DOCX file

        Returns:
        - The root node of the tree
        - The map of ids and nodes
        """
        # Create a temporary file to store the extracted text
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        temp_file_path = temp_file.name
        temp_file.close()
        
        try:
            # Extract text from the DOCX file
            text = docx2txt.process(full_file_path)
            
            # Write the extracted text to the temporary file
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Process the text file using the existing method
            return self.txt_to_structuralGraph(temp_file_path)
        finally:
            # Clean up: remove the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def txt_to_structuralGraph(self, full_file_path):
        """
        Convert a TXT file to a structural graph.
        
        Args:
        - full_file_path: Path to the TXT file

        Returns:
        - The root node of the tree
        - The map of ids and nodes
        """
        # Load the document (local laoder)
        loader = TextLoader(file_path=full_file_path, encoding="utf-8")
        docs = [doc for doc in loader.lazy_load()]
        return self.build_tree(docs)

    def pdf_to_structuralGraph(self, full_file_path):
        """
        Convert a PDF file into a structural graph by extracting text sections.
        
        Args:
        - full_file_path: Path to the PDF file

        Returns:
        - The root node of the tree
        - The map of ids and nodes
        """
        # Load the document (local laoder)
        loader = UnstructuredLoader(file_path=full_file_path, mode="elements", strategy="hi_res",)
        docs = [doc for doc in loader.lazy_load()]
        return self.build_tree(docs)

    def _assign_metadata_to_sections(self, docs, parsed_document):
        """
        Convert parsed sections to SectionWithMetadata and assign metadata.

        Args:
        - docs (List[Document]): The list of parsed document elements.
        - parsed_document (DocumentStructure): The structured document containing sections.

        Returns:
        - A list of SectionWithMetadata instances.
        """
        updated_sections = []  # Store new sections with metadata

        for section in parsed_document.sections:
            # Create a new instance of SectionWithMetadata
            new_section = SectionWithMetadata(
                id=section.id,
                content=section.content,
                parentSectionId=section.parentSectionId,
                metadata={}
            )

            for doc in docs:
                doc_text = doc.page_content.strip()
                if doc_text in section.content:
                    if new_section.metadata == {}:
                        metadata = {
                            key: doc.metadata[key] for key in ['source', 'filename', 'last_modified', 'filetype', 'page_number'] if key in doc.metadata
                        }
                        new_section.metadata = metadata
                    break  

            updated_sections.append(new_section)

        return updated_sections

    def build_tree(self, docs):
        """
        Build a hierarchical tree structure from extracted document sections.

        This function takes a list of extracted document elements (`docs`), processes 
        them into structured sections, and organizes them into a tree structure 
        where each section is assigned a unique ID and may have parent-child 
        relationships.

        Args:
        - docs (List[Document]): A list of extracted document sections, 
        typically obtained from a document parser.

        Returns:
        - Tuple[TreeNode, Dict[int, TreeNode]]: 
        - The root node of the tree (`TreeNode`).
        - A dictionary mapping section IDs to their corresponding `TreeNode` objects.

        Process:
        1. **Concatenate document text**: Combines all extracted sections into a single string.
        2. **Parse the document structure**: Uses an LLM to convert raw text into structured sections.
        3. **Generate a unique document ID**: Ensures each document instance has a distinct identifier.
        4. **Assign metadata to sections**: Enhances sections with metadata extracted from the document.
        5. **Build the tree structure**:
        - Initializes a root node.
        - Iterates through structured sections, assigning each an ID, parent ID, and metadata.
        - Constructs the tree by linking nodes to their parent sections.
        """

        # Step 1: Combine document text for parsing
        document_text = ""
        for doc in docs:
            document_text += '\n' + doc.page_content

        llm = get_llm()

        # Step 2: Parse the document structure using an LLM
        parsed_document = llm.with_structured_output(DocumentStructure).invoke(
            [PARSING_PROMPT.format(document=document_text)]
        )    

        document_summary = parsed_document.summary

        # Ensure the first section has a valid parent ID (root reference)
        parsed_document.sections[0].parentSectionId = 0

        # Step 3: Generate a unique document identifier
        document_id = str(uuid.uuid4())  # Generates a random UUID

        # Step 4: Assign extracted metadata to sections
        sections = self._assign_metadata_to_sections(docs, parsed_document)

        # Step 5: Initialize tree structure
        node_map = {}  # Dictionary to store ID-to-node mappings

        # Insert the root node (the base of the tree)
        root = self.TreeNode(id=0, content="Root Node", parent=None)
        node_map[0] = root  # Register root node

        # Iterate over all sections and construct the tree
        for section in sections:
            section_id = section.id
            parent_id = section.parentSectionId
            content = section.content

            section.metadata["in_document_index"] = section_id
            section.metadata["in_document_parent_index"] = parent_id
            section.metadata["document_summary"] = document_summary
            section.metadata["document_id"] = document_id  # Attach document ID to metadata

            # Find parent node; default to root if not found
            parent_node = node_map.get(parent_id, root)

            # Create a new node and add it to the tree
            node_map[section_id] = self.TreeNode(section_id, content, parent_node, section.metadata)
        
        # Return the root of the tree and the node mapping
        return root, node_map
    
    def find_node_by_content(self, query_text):
        """
        Find the node where the content contains the given query_text as a substring.

        Args:
        - query_text (str): The text to search for.

        Returns:
        - The first matching TreeNode instance, or None if no match is found.
        """
        for node in self.node_map.values():
            if query_text in node.content:  # Checks if query_text is a subset
                return node
        return None  # No match found

    def get_children_by_content(self, query_text):
        """
        Find the node by its content and return its children.

        Args:
        - query_text (str): The text to search for.

        Returns:
        - A list of children nodes, or an empty list if no match is found.
        """
        node = self.find_node_by_content(query_text)
        return node.get_children_of_node() if node else []

    def get_parent_by_content(self, query_text):
        """
        Find the node by its content and return its parent.

        Args:
        - query_text (str): The text to search for.

        Returns:
        - The parent node, or None if no match or if it's the root.
        """
        node = self.find_node_by_content(query_text)
        return node.get_parent_of_node() if node else None

    def get_siblings_by_content(self, query_text):
        """
        Find the node by its content and return its siblings.

        Args:
        - query_text (str): The text to search for.

        Returns:
        - A list of sibling nodes, or an empty list if no match.
        """
        node = self.find_node_by_content(query_text)
        return node.get_siblings_of_node() if node else []

    def get_ancestors_by_content(self, query_text, withoutRoot=False):
        """
        Find the node by its content and return its ancestors.

        Args:
        - query_text (str): The text to search for.
        - withoutRoot (bool): If it set to true, root isnt returned

        Returns:
        - A list of ancestor nodes in order from root to parent, or an empty list if no match.
        """
        node = self.find_node_by_content(query_text)
        return node.get_ancestors_of_node(withoutRoot) if node else []

    def get_descendants_by_content(self, query_text):
        """
        Find the node by its content and return all its descendants.

        Args:
        - query_text (str): The text to search for.

        Returns:
        - A list of descendant nodes (children, grandchildren, etc.), or an empty list if no match.
        """
        node = self.find_node_by_content(query_text)
        return node.get_descendants_of_node() if node else []

    def __repr__(self):
        """Pretty-print the tree structure"""
        return self.root.get_tree_structure() if self.root else "Empty StructuralTree"

    # in the future structural info and contextual info must added to the content of the document
    def convert_tree_to_documents(self):
        """
        Converts all nodes in the structural tree into LangChain `Document` objects.

        Returns:
        - List[Document]: A list of LangChain `Document` objects.
        """

        def _one_doc_per_node():
            """Create a single document per node."""
            documents = []
            def traverse(node):
                if node is None:
                    return

                if node != self.root:
                    metadata = node.metadata.copy() if node.metadata else {}
                    metadata.update({
                        "parsing_method": "structural",
                        "chunking_strategy": "single_node"
                    })

                    content = f"""--- ORIGINAL SPAN OF THE DOCUMENT ---\n{node.content}\n------"""

                    doc = Document(
                        page_content=content,
                        metadata=metadata
                    )
                    documents.append(doc)

                for child in node.children:
                    traverse(child)

            traverse(self.root)
            return documents

        def _include_ancestors():
            """Create a document per node with its ancestor context."""
            documents = []

            def traverse(node):
                if node is None:
                    return

                if node is not self.root:
                    ancestors = node.get_ancestors_of_node(withoutRoot=True)
                    ancestor_texts = [a.content for a in ancestors if a.content]
                    joined_ancestor_texts = "\n".join(ancestor_texts)
                    content = f"""--- STRUCTURAL ANCESTORS OF THE SPAN ---\n{joined_ancestor_texts}\n------\n--- ORIGINAL SPAN OF THE DOCUMENT ---\n{node.content}\n------"""

                    metadata = node.metadata.copy() if node.metadata else {}
                    metadata.update({
                        "parsing_method": "structural",
                        "chunking_strategy": "with_ancestors"
                    })

                    if ancestor_texts:
                        # Only create a document if there are ancestor texts
                        doc = Document(
                            page_content=content,
                            metadata=metadata
                        )
                        documents.append(doc)

                for child in node.children:
                    traverse(child)

            traverse(self.root)
            return documents

        def _include_descendants():
            """Create a document per node with its descendant context."""
            documents = []

            def traverse(node):
                if node is None:
                    return

                descendants = node.get_descendants_of_node()
                descendant_texts = [d.content for d in descendants if d.content]
                
                if node == self.root:
                    content = "\n".join(descendant_texts)
                else:
                    joined_descendant_texts = "\n".join(descendant_texts)
                    content = f"""--- ORIGINAL SPAN OF THE DOCUMENT ---\n{node.content}\n------\n--- STRUCTURAL DESCENDANTS OF THE SPAN ---\n{joined_descendant_texts}\n------\n"""

                metadata = node.metadata.copy() if node.metadata else {}
                metadata.update({
                    "parsing_method": "structural",
                    "chunking_strategy": "with_descendants"
                })

                # Only create a document if there are descendant texts
                if descendant_texts:
                    doc = Document(
                        page_content=content,
                        metadata=metadata
                    )
                
                    documents.append(doc)

                for child in node.children:
                    traverse(child)

            traverse(self.root)
            return documents

        def _remove_duplicates(documents):
            """Remove duplicate documents based on content and essential metadata only."""

            seen = set()
            unique_documents = []

            for doc in documents:
                # Exclude variable metadata keys when comparing
                metadata = doc.metadata.copy()
                metadata.pop("chunking_strategy", None)
                metadata.pop("parsing_method", None)

                key = (doc.page_content.strip(), frozenset(metadata.items()))

                if key not in seen:
                    seen.add(key)
                    unique_documents.append(doc)

            return unique_documents

        documents = []
        documents.extend(_one_doc_per_node()) 
        documents.extend(_include_ancestors())  
        documents.extend(_include_descendants())
        documents = _remove_duplicates(documents)
        return documents

# usage of StructuralTree:

# generate a tree from a PDF file
# myTree = StructuralTree('./original_tuned_copy.pdf')

# generate a tree from a DOCX file
# myTree = StructuralTree('./original_tuned_copy.docx')

# generate a tree from a TXT file
# myTree = StructuralTree('./original_tuned_copy.txt')

# print the tree structure
# print(myTree)
# output:
# - Root Node
# ---- COMMERCIAL SALE AGREEMENT
# ---- THIS COMMERCIAL SALE AGREEMENT (the “Agreement”) is made and entered into on this 15th day of December, 2024, by and between:
# ---- THIS COMMERCIAL SALE AGREEMENT (the “Agreement”) is made and entered into
# ------- SELLER: on this 15th day of December, 2024, by and between:
# ------- Meridian Technologies, Inc. A Delaware Corporation 1234 Innovation

# find a node by its content in the document:
# node = myTree.find_node_by_content('supplier agreements, and other contractual')
# print(node)

# traverse the tree with root the current node:
# print(node.get_tree_structure())

# get the parent by content:
# print(myTree.get_parent_by_content('(a) An initial deposit of Five Million'))

# get the children by content:
# print(myTree.get_children_by_content('Seller represents and warrants to Buyer'))

# get the siblings by content:
# print(myTree.get_siblings_by_content('duly organized and validly existing under the laws'))

# get the ancestors by content:
# print(myTree.get_ancestors_by_content('All technical documentation, manufacturing processes, and related know- how')) [withoutRoot=True doesnt return the root]

# convert the tree to documents:
# docs = myTree.convert_tree_to_documents()

class StructuralParser:

    def __init__(self):
        pass

    def parse_document(self, file_path: str) -> List[Document]:

        myTree = StructuralTree(file_path)

        docs = myTree.convert_tree_to_documents()

        return docs