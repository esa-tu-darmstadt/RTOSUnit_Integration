import cocotb
from cocotb.binary import BinaryValue
from typing import Optional

# Version 2023-09-18

# Error handling is not optimal (MemViewErrors aren't passed through HierarchicalMemView)

class MemViewError(Exception):
    pass

def _extend_word(_st, word : BinaryValue, n_word_bits, big_endian) -> BinaryValue:
    if word.n_bits < n_word_bits:
        if (n_word_bits & 7) != 0 or (word.n_bits & 7) != 0:
            raise MemViewError("Word length is not in full bytes")
        # TODO: Does this work with big endian?

        word_new = BinaryValue(n_bits=n_word_bits, bigEndian=big_endian)
        for i in range(0, n_word_bits, word.n_bits):
            word_new[i+word.n_bits-1:i] = str(word)

        return word_new
    return word

# MemView base class, can be instantiated with callbacks that handle reads and writes.
class MemView():
    # read_cb: (start byte position, one-beyond-last byte position, is big endian: bool)
    # write_cb: (start byte position, one-beyond-last byte position, word: bytes, wstrb: BinaryValue)
    def __init__(self, read_cb=None, write_cb=None):
        self._read_cb = read_cb
        self._write_cb = write_cb

    def _write(self, _st, _end, word : BinaryValue, wstrb : BinaryValue) -> bool | MemViewError:
        return (self._write_cb is not None) and self._write_cb(_st,_end,word,wstrb)

    def _read(self, _st, _end, n_word_bits, big_endian) -> BinaryValue | None | MemViewError:
        if self._read_cb is None:
            return None
        word_data = self._read_cb(_st,_end,big_endian)
        if word_data is None:
            return None
        word = BinaryValue(n_bits=(_end-_st)*8, bigEndian=big_endian)
        word.buff = bytes(word_data)
        return word

    # Public: Writes a word into the memory view in range [_st,_end). Can raise a MemViewError.
    # wstrb: For each byte in word, wstrb[i] indicates whether the new byte should be written.
    def write(self, _st, _end, word : bytes, wstrb : BinaryValue):
        res = self._write(_st, _end, word, wstrb)
        if res == False:
            raise MemViewError("Write to address 0x%08x failed: No matching handler" % _st)
        if isinstance(res, MemViewError):
            raise res

    # Public: Reads a word from the memory view. Can raise a MemViewError.
    # n_word_bits: The number of bits the output word has (must be a multiple of 8).
    def read(self, _st, _end, n_word_bits, big_endian : bool = False) -> BinaryValue:
        res = self._read(_st, _end, n_word_bits, big_endian)
        if res is None:
            raise MemViewError("Read from address 0x%08x failed: No matching handler" % _st)
        if isinstance(res, MemViewError):
            raise res
        return _extend_word(_st, res, n_word_bits, big_endian)

# MemView backed by a bytearray, with optional callbacks.
class BytearrayMemView(MemView):
    def __init__(self, memory : bytearray, memory_section_offs=0, memory_section_len=-1, memory_baseaddr=0,
            read_cb=None, write_cb=None, auto_resize=False):
        MemView.__init__(self, read_cb, write_cb)
        self.memory = memory
        self.memory_section_offs = memory_section_offs
        if memory_section_len == -1:
            memory_section_len = len(memory) - memory_section_offs
        self.memory_section_len = memory_section_len
        self.memory_baseaddr = memory_baseaddr
        self.auto_resize = auto_resize

    def _write(self, _st, _end, word : bytes, wstrb) -> bool | MemViewError:
        base_res = MemView._write(self,_st,_end,word,wstrb)
        if base_res == True:
            return True
        if _st < self.memory_baseaddr or _end > self.memory_baseaddr + self.memory_section_len:
            return MemViewError("Write to address 0x%08x: Out of range [%08x,%08x)" % (_st, self.memory_baseaddr, self.memory_baseaddr + self.memory_section_len))
        memoryarr_startoffs = _st - self.memory_baseaddr + self.memory_section_offs
        memoryarr_endoffs = _end - self.memory_baseaddr + self.memory_section_offs
        if memoryarr_endoffs > len(self.memory):
            if not self.auto_resize:
                return MemViewError("Write to address 0x%08x out of bounds of backing array (%08x > %08x)" % (_st, memoryarr_endoffs, len(self.memory)))
            self.memory += bytearray(memoryarr_endoffs - len(self.memory))
        for i in range(len(wstrb)):
            if wstrb[i] == 0:
                word[i] = self.memory[memoryarr_startoffs + i]
        self.memory[memoryarr_startoffs : memoryarr_endoffs] = word
        return True

    def _read(self, _st, _end, n_word_bits, big_endian) -> BinaryValue | None | MemViewError:
        base_res = MemView._read(self,_st,_end,n_word_bits,big_endian)
        if isinstance(base_res, BinaryValue):
            print("Read from address 0x%08x -> %s (callback)" % (_st, str(base_res.buff)))
            return base_res
        word = BinaryValue(n_bits=(_end-_st)*8, bigEndian=big_endian)
        if _st < self.memory_baseaddr or _end > self.memory_baseaddr + self.memory_section_len:
            return MemViewError("Read from address 0x%08x: Out of range [%08x,%08x)" % (_st, self.memory_baseaddr, self.memory_baseaddr + self.memory_section_len))
        memoryarr_startoffs = _st - self.memory_baseaddr + self.memory_section_offs
        memoryarr_endoffs = _end - self.memory_baseaddr + self.memory_section_offs
        if memoryarr_endoffs > len(self.memory):
            if not self.auto_resize:
                return MemViewError("Read from address 0x%08x: Out of bounds of backing array (%08x > %08x)" % (_st, memoryarr_endoffs, len(self.memory)))
            self.memory += bytearray(memoryarr_endoffs - len(self.memory))
        word.buff = bytes(self.memory[memoryarr_startoffs : memoryarr_endoffs])
        return word

# MemView backed by several child MemViews, with optional callbacks.
class HierarchicalMemView(MemView):
    def __init__(self, children,
            read_cb=None, write_cb=None):
        MemView.__init__(self, read_cb, write_cb)
        self.children = children

    def _write(self, _st, _end, word : bytes, wstrb) -> bool | MemViewError:
        base_res = MemView._write(self,_st,_end,word,wstrb)
        if base_res == True:
            return True
        for child in self.children:
            child_res = child._write(_st,_end,word,wstrb)
            if child_res == True:
                return True
        return False

    def _read(self, _st, _end, n_word_bits, big_endian) -> BinaryValue | None | MemViewError:
        base_res = MemView._read(self,_st,_end,n_word_bits,big_endian)
        if isinstance(base_res, BinaryValue):
            return base_res
        for child in self.children:
            child_res = child._read(_st,_end,n_word_bits,big_endian)
            if isinstance(child_res, BinaryValue):
                return child_res
        return None

