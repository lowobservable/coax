// Copyright (c) 2020, Andrew Kay
//
// Permission to use, copy, modify, and/or distribute this software for any
// purpose with or without fee is hereby granted, provided that the above
// copyright notice and this permission notice appear in all copies.
//
// THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
// WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
// ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
// WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
// ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
// OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

#pragma once

// The coax buffer size is based on the maximum receive size, which as a
// controller should be limited.
#define COAX_BUFFER_SIZE 32

// The message buffer size is based on the maximum conceivable coax write
// data command length which in turn assumes a maximum regen and EAB buffer
// being written in a single command.
#define MAX_COAX_WRITE_SIZE (1 + (3696 * 2))

#define MESSAGE_BUFFER_SIZE ((MAX_COAX_WRITE_SIZE * sizeof(uint16_t)) + 32)
