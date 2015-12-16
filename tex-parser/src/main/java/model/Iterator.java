package model;

import java.util.List;

/**
 * An iterator to iterate a list of elements.
 *
 * @param <T> The type to iterate.
 * 
 * @author Claudius Korzen
 */
public class Iterator<T> implements java.util.Iterator<T> {
  /** The elements to iterate. */
  protected List<T> elements;
  /** The location where to start. */
  protected String start;
  /** The location where to end. */
  protected String end;
  /** The current index. */
  public int currentIndex;

  /**
   * The default constructor.
   */
  public Iterator(List<T> elements) {
    this.elements = elements;
  }
  
  /**
   * The default constructor.
   */
  public Iterator(List<T> elements, String start, String end) {
    this(elements);
    this.start = start;
    this.end = end;
    if (start != null) {
      skipTo(start);
    }
  }

  @Override
  public boolean hasNext() {
    return currentIndex < elements.size()
        && elements.get(currentIndex) != null
        && !elements.get(currentIndex).toString().equals(end);
  }

  @Override
  public T next() {
    return elements.get(currentIndex++);
  }

  /**
   * Returns the next element without incrementing the position cursor.
   */
  public T peek() {
    return elements.get(currentIndex);
  }

  @Override
  public void remove() {
    throw new UnsupportedOperationException();
  }

  /**
   * Skips to the element, given as string.
   */
  public void skipTo(String elementStr) {
    if (elementStr != null) {
      while (hasNext()) {
        T el = next();
        if (el.toString().equals(elementStr)) {
          break;
        }
      }
    }
  }
}
