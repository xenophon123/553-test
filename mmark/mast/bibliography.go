package mast

import (
	"github.com/mmarkdown/mmark/mast/reference"

	"github.com/gomarkdown/markdown/ast"
)

// Bibliography represents markdown bibliography node.
type Bibliography struct {
	ast.Container

	Type ast.CitationTypes
}

// BibliographyItem contains a single bibliography item.
type BibliographyItem struct {
	ast.Leaf

	Anchor []byte
	Type   ast.CitationTypes

	Reference *reference.Reference // parsed reference XML
}
