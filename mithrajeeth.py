from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf():
    pdf_filename = "mithrajeeth.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter,
                            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        alignment=1,
        textColor=colors.HexColor("#1A365D")
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#4A5568")
    )
    
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=5
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748")
    )

    story.append(Paragraph("Model Context Protocol (MCP) vs. Retrieval-Augmented Generation (RAG)", title_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph("A Comprehensive One-Page Comparison for Modern AI Systems", subtitle_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("1. Executive Summary", heading_style))
    summary_text = (
        "Both <b>MCP (Model Context Protocol)</b> and <b>RAG (Retrieval-Augmented Generation)</b> bridge the gap "
        "between large language models (LLMs) and external data sources. However, they serve fundamentally different architectural "
        "purposes: RAG focuses on <i>knowledge retrieval</i> from large document corpora to answer domain-specific questions, "
        "while MCP provides a standardized <i>client-server protocol</i> for real-time tool execution, resource reading, and agentic interaction."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. Core Concepts & Definitions", heading_style))
    concepts_text = (
        "<b>RAG:</b> A pattern where an external database (often a vector store) is queried using a user prompt. Relevant chunks "
        "are retrieved and injected into the LLM context window so the model can synthesize an informed answer.<br/>"
        "<b>MCP:</b> An open standard created by Anthropic that standardizes how AI models connect to data sources and tools. "
        "It establishes a secure client-server architecture allowing models to dynamically list tools, read files, and interact with APIs."
    )
    story.append(Paragraph(concepts_text, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("3. Detailed Feature Comparison", heading_style))
    
    table_data = [
        [
            Paragraph("<b>Dimension</b>", body_style),
            Paragraph("<b>Retrieval-Augmented Generation (RAG)</b>", body_style),
            Paragraph("<b>Model Context Protocol (MCP)</b>", body_style)
        ],
        [
            Paragraph("<b>Primary Goal</b>", body_style),
            Paragraph("Retrieve relevant text documents / data to augment model knowledge.", body_style),
            Paragraph("Standardize integration with local/remote tools, prompts, and resources.", body_style)
        ],
        [
            Paragraph("<b>Primary Action</b>", body_style),
            Paragraph("Read-only search & retrieval (Semantic vector search / BM25).", body_style),
            Paragraph("Bi-directional interaction: read resources, call tools, execute actions.", body_style)
        ],
        [
            Paragraph("<b>Architecture</b>", body_style),
            Paragraph("Pipeline: Embed query -> Vector DB search -> Context stuffing -> LLM.", body_style),
            Paragraph("Client-Server protocol (JSON-RPC over stdio/SSE).", body_style)
        ],
        [
            Paragraph("<b>Use Cases</b>", body_style),
            Paragraph("Enterprise Q&A, searching internal wikis, documentation bots, semantic search.", body_style),
            Paragraph("IDE assistants (Cursor/Claude), executing terminal commands, querying live DBs, interacting with APIs.", body_style)
        ],
        [
            Paragraph("<b>Statefulness</b>", body_style),
            Paragraph("Stateless request-response per query.", body_style),
            Paragraph("Can maintain persistent server connections and context streams.", body_style)
        ]
    ]

    t = Table(table_data, colWidths=[90, 230, 230])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("4. Synergy: Can They Work Together?", heading_style))
    synergy_text = (
        "<b>Yes, they are complementary!</b> An AI agent powered by MCP can use an <b>MCP server</b> to execute a RAG query "
        "against an enterprise vector database when deep document search is required, while simultaneously using other MCP servers "
        "to write code, query databases, or execute actions. MCP provides the universal plumbing, and RAG provides the search engine."
    )
    story.append(Paragraph(synergy_text, body_style))

    doc.build(story)
    print("PDF generated successfully.")

if __name__ == '__main__':
    generate_pdf()
