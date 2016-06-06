package identifier;

import static model.TeXParagraphParserConstants.TMP_TEX_EXTENSIONS;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import de.freiburg.iif.path.PathUtils;
import model.Document;
import model.TeXFile;
import model.TeXParagraph;
import parse.ParseException;
import parse.TeXParser;
import parser.TeXParagraphsParser;
import preprocess.TeXMacroResolver;

/**
 * Class to manage the identification of text paragraphs from tex files.
 * Actually, this is a higher level class for {@link TeXParagraphsParser} that
 * sets up all the necessary stuff for the parser.  
 * 
 * @author Claudius Korzen
 */
public class TeXParagraphsIdentifier {
  /** The tex file to process. */
  protected TeXFile texFile;

  /**
   * Creates a new paragraphs identifier for the given tex file.
   */
  public TeXParagraphsIdentifier(TeXFile file) {
    this.texFile = file;
  }

  /**
   * Starts the identification of tex paragraphs: (1) Resolves the macros 
   * in the given tex file and (2) identifies the paragraphs within the 
   * resolved file.
   */
  public void identify() throws IOException {
    resolveMacros(this.texFile);
    identifyTeXParagraphs(this.texFile);
  }

  // ===========================================================================

  /**
   * Resolves the macros for the given tex file.
   */
  protected void resolveMacros(TeXFile texFile) throws IOException {
    Path texPath = texFile.getPath();
    // Obtain the target file for this step.
    Path tmpPath = defineResolveMacrosTargetFile(texPath);

    resolveMacros(texPath, tmpPath);

    texFile.setTmpPath(tmpPath);
  }

  /**
   * Resolves the macros for the given tex file and writes the resolved file to
   * given target path.
   */
  protected void resolveMacros(Path file, Path targetPath) throws IOException {
    InputStream stream = Files.newInputStream(file);

    try {
      new TeXMacroResolver(stream).resolveMacros(targetPath);
    } catch (ParseException e) {
      throw new IOException(e);
    } finally {
      stream.close();
    }
  }

  // ---------------------------------------------------------------------------

  /**
   * Identifies the text paragraphs in the given tex file.
   */
  protected void identifyTeXParagraphs(TeXFile texFile) throws IOException {
    // Parse the tex file.
    Document document;
    try {
      document = parseTexFile(texFile);
    } catch (ParseException e) {
      throw new IOException(e);
    }

    // Identify the paragraphs in parsed document.
    texFile.setTeXParagraphs(identifyTeXParagraphs(document));
  }

  /**
   * Identifies the paragraphs in the given document.
   */
  protected List<TeXParagraph> identifyTeXParagraphs(Document document)
    throws IOException {
    return new TeXParagraphsParser(document).identifyParagraphs();
  }

  // ---------------------------------------------------------------------------

  /**
   * Parses the given tex file into a new Document object.
   */
  protected Document parseTexFile(TeXFile texFile) throws IOException,
    ParseException {
    return parseTexFile(texFile.getTmpPath());
  }

  /**
   * Parses the given tex file into a new Document object.
   */
  protected Document parseTexFile(Path texPath)
    throws IOException, ParseException {
    InputStream input = Files.newInputStream(texPath);

    Document document;
    try {
      TeXParser parser = new TeXParser(input);
      document = parser.parse();
    } catch (Exception e) {
      throw e;
    } finally {
      input.close();
    }

    return document;
  }

  // ===========================================================================
  // Intermediate file paths definitions.

  /**
   * Obtains the path to the target file for the preprocessing step.
   */
  protected Path defineResolveMacrosTargetFile(Path texFile) {
    // Obtain the basename of the file.
    String basename = PathUtils.getBasename(texFile);
    // Obtain the filename for the target file.
    String filename = basename + TMP_TEX_EXTENSIONS.get(0);
    Path targetDir = defineResolveMacrosTargetDirectory(texFile);
    if (targetDir != null) {
      return targetDir.resolve(filename);
    }
    return null;
  }

  /**
   * Defines the path to the target directory for the preprocessing step.
   */
  protected Path defineResolveMacrosTargetDirectory(Path texFile) {
    return texFile.getParent();
  }
}
