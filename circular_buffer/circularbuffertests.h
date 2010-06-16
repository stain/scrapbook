/* Tests for CircularBuffer.h
 *
 * To compile these tests, you need cxxtest, available
 * at http://cxxtest.sourceforge.net/
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


#include <cxxtest/TestSuite.h>
#include "CircularBuffer.h"

class CircularBufferTests : public CxxTest::TestSuite {
public:
	
    void testCircular() {
		const int size=15;
		CircularBuffer<int> buf(size);
		for (int i=0; i<size; i++) {
			// By default int constructor
			TS_ASSERT_EQUALS(buf[i], 0);
		}
		for (int i=0; i<size; i++) {
			buf.push(i);
			TS_ASSERT_EQUALS(buf[0], i);
		}
		for (int i=0; i<size; i++) {
			// 14 should be in pos 0, etc. till 0 in pos 14
			TS_ASSERT_EQUALS(buf[i], size-i-1);
		}
		// Should now clear away previous values
		for (int i=0; i<size; i++) { buf.push(0); }
		for (int i=0; i<size; i++) {
			TS_ASSERT_EQUALS(buf[i], 0);
		}		
	}
};
