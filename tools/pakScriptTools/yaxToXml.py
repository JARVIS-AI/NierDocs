from __future__ import annotations
from io import BufferedReader
import struct
import sys
from typing import List
import xml.dom.minidom
from xml.etree.ElementTree import Element, SubElement, tostring as xmlToString

def read_uint32(file) -> int:
	entry = file.read(4)
	return struct.unpack('<I', entry)[0]

def read_uint8(file) -> int:
	entry = file.read(1)
	return struct.unpack('<B', entry)[0]

def read_string(file: BufferedReader, pos) -> str:
	initialPos = file.tell()
	file.seek(pos)
	binaryString = b""
	while True:
		char = file.read(1)
		if char == b'\x00':
			break
		binaryString += char
	file.seek(initialPos)
	return binaryString.decode('shift-jis')

def getTagName(id: int) -> str:
	return "UNKNOWN"

class XmlNode:
	indentation: int
	tag: str
	value: str

	children: List[XmlNode]

	def __init__(self, file: BufferedReader = None):
		self.indentation = -1
		self.tag = ""
		self.value = ""
		self.children = []
		if not file:
			return
		self.indentation = read_uint8(file)
		tagId = read_uint32(file)
		self.tag = getTagName(tagId)
		valueOffset = read_uint32(file)
		if valueOffset != 0:
			self.value = read_string(file, valueOffset)
	
	def __str__(self):
		return f"{'    ' * self.indentation}{self.tag}: {self.value}"
	
	def toXml(self) -> Element:
		element = Element(self.tag)
		element.text = self.value
		for child in self.children:
			element.append(child.toXml())
		return element


yaxFile = sys.argv[1] #if len(sys.argv) > 1 else "D:\\delete\\mods\\na\\blender\\extracted\\data012.cpk_unpacked\\st5\\nier2blender_extracted\\r501.dat\\pakExtracted\\r501_hap.pak\\0.yax"

with open(yaxFile, "rb") as f:
	nodeCount = read_uint32(f)
	
	# read flat tree
	nodes: List[XmlNode] = []
	for i in range(nodeCount):
		nodes.append(XmlNode(f))
	
	# assemble tree from indents
	rootNode = XmlNode()
	rootNode.tag = "root"
	for node in nodes:
		if node.indentation == 0:
			rootNode.children.append(node)
			continue
		targetIndent = node.indentation - 1
		parent = rootNode.children[-1]
		while parent.indentation != targetIndent:
			parent = parent.children[-1]
		parent.children.append(node)

	# write xml
	rootXml = rootNode.toXml()
	rawXmlStr = xmlToString(rootXml)
	if type(rawXmlStr) == bytes:
		xmlStr = rawXmlStr.decode("utf-8")
		print("Warning: using fallback string representation")
	dom = xml.dom.minidom.parseString(xmlStr)
	xmlStr = dom.toprettyxml(indent="\t")
	
	with open(f"{yaxFile}.xml", "w", encoding="utf-8") as f:
		f.write(xmlStr)

	