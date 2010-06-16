/**
 * Test no.soiland.lang.IterableIterator
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

import static no.soiland.lang.IterableIterator.iterate;

import java.util.ArrayList;
import java.util.Enumeration;
import java.util.Iterator;
import java.util.List;
import java.util.ListIterator;
import java.util.Vector;

import junit.framework.TestCase;

public class TestIterableIterator extends TestCase {

	Iterator<String> makeStringIterator() {
		List<String> list = new ArrayList<String>();
		list.add("Hello");
		list.add("there");
		return list.iterator();
	}

	ListIterator<Integer> makeListIterator() {
		List<Integer> list = new ArrayList<Integer>();
		list.add(1337);
		list.add(2006);
		return list.listIterator();
	}

	public void testStringIterator() {
		Iterator<String> it = makeStringIterator();
		List<String> copied = new ArrayList<String>();
		for (String s : iterate(it)) {
			copied.add(s);
		}
		assertEquals(2, copied.size());
		assertEquals("Hello", copied.get(0));
		assertEquals("there", copied.get(1));
	}

	public void testListIterator() {
		ListIterator<Integer> it = makeListIterator();
		// Play with the list iterator
		assertFalse(it.hasPrevious());
		it.next();
		assertTrue(it.hasPrevious());
		it.previous();
		assertFalse(it.hasPrevious());
		// We're at the beginning, let's iterate!
		for (int i : iterate(it)) {
			if (i == 1337) {
				it.remove();
				break;
			}
		}
		// 1337 should break, and so the next should be 2006
		int i = it.next();
		assertEquals(2006, i);
		// 2006 is the previous, and last
		assertFalse(it.hasNext());
		assertTrue(it.hasPrevious());
		// Step back..
		it.previous();
		// But 1337 is gone
		assertFalse(it.hasPrevious());
	}
	
	public void testFailsSecondTime() {
		Iterator<String> it = makeStringIterator();
		Iterable<String> itt = iterate(it);
		String total = "";
		for (String s : itt) {
			total = total + s;
		}
		assertEquals("Hellothere", total);
		try {
			for (String s : itt) {
				total = total + s;
			}
			fail("Should throw IllegalStateException");
		} catch (IllegalStateException ex) {
			// OK, return
		}
		// However, another iterator is OK, but it will be at the end
		for (String s : iterate(it)) {
			fail("Iterator should be finished, but got: " + s);
		}
	}
	
	public void testEnumerator() {
		Vector<String> strings = new Vector<String>();
		strings.add("First");
		strings.add("Second");
		String joined = "";
		Enumeration<String> enumeration = strings.elements();
		for (String s : iterate(enumeration)) {
			joined += s;
		}
		assertEquals("FirstSecond", joined);
	}

	
}
