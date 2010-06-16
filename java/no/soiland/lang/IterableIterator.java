/**
 * Wrap an Iterator or Enumerator so that it becomes Iterable and can be used in loops.
 * 
 * <p>
 * Example:
 *   <pre> 
 *   import static no.soiland.lang.IterableIterator.iterate;
 *   Iterator<MyClass> it = getSomeIterator();
 *   for (MyClass o: iterate(it)) {
 *       System.out.println(o);
 *   }
 *  </pre>
 *  
 * <small>
 * Copyright (c) 2006 Stian Soiland
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be included
 * in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 * CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 * TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 * URL: http://soiland.no/i/src/java/
 * License: MIT
 * </small>
 *
 * @author Stian Soiland <stian@soiland.no>
 */


package no.soiland.lang;

import java.util.Enumeration;
import java.util.Iterator;


public class IterableIterator<T> implements Iterable<T> {
	
	private Iterator<T> it;  
    
	/** 
	 * Make an Iterator iterable.
	 * This sounds silly, but it is not possible by default to do
	 * <pre>
	 * Iterator<String> it =  getMyIterator();
	 * for (String s: getMyIterator()) { .. } 
	 * </pre>
	 * 
	 * This method transforms the Iterator into an Iterable that can return the original Iterator. Thus:
	 * <pre>
	 * Iterator<String> it =  getMyIterator();
	 * for (String s: iterate(getMyIterator())) { .. }
	 * </pre>
	 * 
	 * 
	 * @param <V> The type of the Iterator and Iterable.
	 * @param it an Iterator that is to be wrapped
	 * @return an Iterable that can return the iterator.
	 */
    public static <V> Iterable<V> iterate(Iterator<V> it) {
	    return new IterableIterator<V>(it);     
	} 
    
    /**
     * Make an Enumeration iterable, similar to iterate(Iterator<V> it).
     * 
     * @param <V> Type of Enumeration and returned Iterable.
     * @param enumeration  An Enumeration, as returned by ancient java.util.Vector, etc.
     * @return An Iterable to be used in for(V s: iterate(en)) syntax
     */
    public static <V> Iterable<V> iterate(final Enumeration<V> enumeration) {
    	// Proxy the enumeration as an iterator
    	// TODO: Is this proxy also wanted in the lang class?
    	Iterator<V> it = new Iterator<V>() {
			public boolean hasNext() {
				return enumeration.hasMoreElements();				
			}
			public V next() {
				return enumeration.nextElement();
			}
			public void remove() {
				throw new UnsupportedOperationException();				
			}    	
    	};
	    return new IterableIterator<V>(it);     
	} 
    
    /**
     * Non-public constructor, must use one of the static methods.
     */
	IterableIterator(Iterator<T> it) {
        this.it = it;
    }
    
	/**
	 * Return the initial iterator. Note that this can only be called
	 * once.
	 */
	public synchronized Iterator<T> iterator() {            
        Iterator<T> it = this.it;
        if (it == null) {
        	throw new IllegalStateException();
        }
        // Can only return the iterator once, return null after that
        this.it = null;
        return it;
    }   
}

