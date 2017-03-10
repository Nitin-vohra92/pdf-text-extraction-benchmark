from utils import iterators

from models import tex_elements
from models import doc_elements
from models import rules


def identify_ltb_outline(doc, rules_path):
    """
    Iterates through the elements of the given TeX document and identifies the
    logical text blocks (LTBs) based on the given rules.

    Args:
        doc (TeXDocument): The parsed TeX document.
        rules_path (str): The path to the rules file to use.

    Returns:
        The (hierarchical) outline of identified LTBs.
    """
    # Read the rules from file.
    rules_obj = rules.Rules.read_from_file(rules_path)
    # Identify the logical text blocks.
    return LTBIdentifier(doc, rules_obj).identify()


class LTBIdentifier():
    """
    A class to identify the LTBs of TeX documents based on rules.
    """

    def __init__(self, doc, rules_obj):
        """
        Creates a new LTB identifier.

        Args:
            doc (TeXDocument): The parsed TeX document.
            rules (Rules): The rules to use on identifying the LTBs.
        """
        self.doc = doc
        self.rules = rules_obj

    def identify(self):
        """
        Identifies the LTBs in the given TeX document.

        Returns:
            The (hierarchical) outline of the identified LTBs.
        """
        return self.identify_blocks(self.doc.elements)

    def identify_blocks(self, elements):
        """
        Iterates through the given elements in order to identify LTBs using the
        rules of this identifier.

        Args:
            elements (list of TeXElement): The elements to process.
        Returns:
            The identified (hierarchical) outline of the LTBs.
        """

        # Create a context object, containing the parent TeX document, the
        # current hierarchical level, the stack of unfinished LTBs, the
        # outline of finished LTBs and the current environment stack.
        context = Context(
            document=self.doc,
            level=0,
            stack=[doc_elements.LTB(level=0)],
            outline=doc_elements.LTBOutline(),
            environment_stack=[]
        )

        # Interpret the elements in the given document.
        self._identify_blocks(elements, context)

        return context.finalize_outline()

    def _identify_blocks(self, elements, context):
        """
        Iterates through the given elements in order to identify LTBs using the
        given context.

        Args:
            elements (list of TeXElement): The elements to process.
            context (Context): The current context.
        """
        # Iterate the elements in a shallow way (deeper traversals may be
        # defined by individual rules).
        itr = iterators.ShallowIterator(elements)
        for elem in itr:
            if isinstance(elem, tex_elements.TeXWord):
                # Append text to the active block.
                context.append_text(elem.text)

            if isinstance(elem, tex_elements.TeXGroup):
                # Interpret all elements of the group.
                self._identify_blocks(elem.elements, context)

            if isinstance(elem, tex_elements.TeXCommand):
                # Interpret the command correspondingly to referring rule.
                # Obtain the referring rule.
                rule = self.rules.get_rule(elem, context)

                if rule is None:
                    # There is no such rule. Ignore the command.
                    if isinstance(elem, tex_elements.TeXBeginEnvironmentCommand):
                        # If the command begins an environment, skip the entire
                        # environment.
                        itr.skip_to_element(elem.end_command)
                    continue

                # Process each single instruction given by the rule.
                for instruction in rule.instructions:
                    instruction.apply(self, itr, elem, context)


class Context:
    """
    A class representing the context while identifying LTBs.
    """
    def __init__(self, document=None, level=0, stack=[], outline=None,
                 environment_stack=[]):
        """
        Creates a new context.

        Args:
            document (TeXDocument): The parent TeX document.
            level (int): The current hierarchical level.
            stack (stack of LTB): The stack of unfinished LTBs.
            outline (LTBOutline): The outline of finished LTBs.
            environment_stack (stack of str): The stack of environment names.
        """
        self.document = document
        self.level = level
        self.stack = stack
        self.outline = outline
        self.environment_stack = environment_stack

    def introduce_block(self):
        """
        Appends a new block with the current hierarchy level to stack of
        unfinished blocks.
        """
        block = doc_elements.LTB(level=self.level)
        self.stack.append(block)

    def finish_block(self):
        """
        Pops the topmost block from stack of unfinished blocks and adds it, if
        its text is non-empty, to the outline of finished blocks.
        """
        if len(self.stack) == 0:
            return
        block = self.stack.pop()
        if not block.has_text():
            return
        self.outline.append(block)

    def set_hierarchy_level(self, level):
        """
        Sets the current hierarchy level to the given level.

        Args:
            level (int): The level to set.
        """
        self.level = level

    def set_semantic_role(self, role):
        """
        Sets the semantic role of topmost block in the stack of unfinished
        blocks.

        Args:
            role (str): The role to set.
        """
        if len(self.stack) > 0:
            self.stack[-1].semantic_role = role

    def register_whitespace(self):
        """
        Registers a whitespace to the topmost block in the stack of unfinished
        blocks.
        """
        if len(self.stack) > 0:
            self.stack[-1].register_whitespace()

    def append_text(self, text):
        """
        Appends the given text to the topmost block in the stack of unfinished
        blocks.

        Args:
            text (str): The text to append.
        """
        if len(self.stack) > 0:
            self.stack[-1].append_text(text)

    def begin_environment(self, environment):
        """
        Begins an environment.

        Args:
            environment (str): The name of the environment to begin.
        """
        self.environment_stack.append(environment)

    def end_environment(self, environment):
        """
        Ends an environment.

        Args:
            environment (str): The name of the environment to end.
        """
        self.environment_stack.pop()

    def finalize_outline(self):
        """
        Removes the remaining LTBs from the stack and appends them to the
        outline.

        Returns:
            The outline after the remaining LTBs in the stack were added.
        """
        while len(self.stack) > 0:
            block = self.stack.pop()
            if block.has_text():
                self.outline.append(block)
        return self.outline
