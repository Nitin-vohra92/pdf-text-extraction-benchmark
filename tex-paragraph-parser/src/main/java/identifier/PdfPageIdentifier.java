package identifier;

import static de.freiburg.iif.affirm.Affirm.affirm;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageTree;
import org.apache.pdfbox.pdmodel.common.PDRectangle;

import de.freiburg.iif.model.Rectangle;
import de.freiburg.iif.model.simple.SimpleRectangle;
import model.TeXFile;

/**
 * Identifies the bounding boxes of pdf pages.
 */
public class PdfPageIdentifier {
  /**
   * The tex file to process.
   */
  protected TeXFile texFile;
  
  /** 
   * The bounding boxes of pages. 
   */
  protected List<Rectangle> pageBoundingBoxes;
  
  /**
   * Creates a new pdf page identifier.
   */
  public PdfPageIdentifier(TeXFile texFile) {
    this.texFile = texFile;
  }
  
  /**
   * The coordinates provided by synctex are relative to the upper left, but we
   * need coordinates relative to the lower left. Hence, we have to adapt the
   * coordinates. For that we need to know the dimensions of each page.
   */
  protected List<Rectangle> loadPageBoundingBoxes(TeXFile texFile) {
    List<Rectangle> pageBoundingBoxes = new ArrayList<>();

    try {
      Path pdfPath = texFile.getPdfPath();
      PDDocument pdDocument = PDDocument.load(pdfPath.toFile());
      PDPageTree pages = pdDocument.getDocumentCatalog().getPages();
      pageBoundingBoxes = new ArrayList<>();
      pageBoundingBoxes.add(null); // add dummy because pages are 1-based.

      // Compute the bounding boxes.
      for (PDPage page : pages) {
        Rectangle boundingBox = new SimpleRectangle();

        PDRectangle box = page.getCropBox();
        if (box == null) {
          box = page.getMediaBox();
        }
        if (box != null) {
          boundingBox.setMinX(box.getLowerLeftX());
          boundingBox.setMinY(box.getLowerLeftY());
          boundingBox.setMaxX(box.getUpperRightX());
          boundingBox.setMaxY(box.getUpperRightY());
        }

        pageBoundingBoxes.add(boundingBox);
      }
      pdDocument.close();
    } catch (IOException e) {
      throw new IllegalStateException("Couldn't load the pdf file.", e);
    }

    return pageBoundingBoxes;
  }
  
  // ===========================================================================
  
  /**
   * Returns the bounding box of given page.
   */
  public Rectangle getBoundingBox(int pageNum) {    
    if (this.pageBoundingBoxes == null) {
      // Load the bounding boxes of pages.
      this.pageBoundingBoxes = loadPageBoundingBoxes(texFile);
    }
    
    affirm(pageNum > 0, "The page number is too small");
    affirm(pageNum < pageBoundingBoxes.size(), "The page number is too large");
    
    return this.pageBoundingBoxes.get(pageNum);
  }
}
