/* Circular buffer
 *
 * A circular buffer of size N where you can add new elements, and
 * retrieve the N latest added elements. Older elements are
 * automatically removed.
 *
 * Inspired by the Python module circbuf.py from NAV, available at
 * http://svn.itea.ntnu.no/repos/nav/navme/trunk/subsystem/statemon/nav/statemon/circbuf.py
 *
 * Copyright (c) 2005 Stian Soiland
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
 * Author: Stian Soiland <stian@soiland.no>
 * URL: http://soiland.no/i/src/
 * License: MIT
 *
 */

#ifndef _CIRCULAR_BUFFER_H
#define _CIRCULAR_BUFFER_H

#include <vector>
#include <cassert>

template <class T>
class CircularBuffer {
private:
	typedef typename std::vector<T> buf_type;
	buf_type buffer;
	int size;
	// Last position push()-ed to
	int pos;
public:
	/* Create the buffer of the given size. 
	 */
	CircularBuffer(int size) : buffer(size), size(size), pos(0) {
	}
	
	/* Retrieve element inserted N push()-es ago.
	 * circbuf[0] will be the last element pushed, 
	 * circbuf[1] the element before that, etc.
	 */
	T& operator[](int i) {
		assert(i >= 0);
		assert(i < size);
		i = (size + pos - i) % size;
		return buffer[i];
	}
        /* Push element onto the front of the buffer.
         */
	void push(const T &obj) {
		pos = (pos+1) % size;
		buffer[pos] = obj;
 	}
};

#endif
