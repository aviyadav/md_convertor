def md2pdf(md_file: str, output_file: str):
    from markdown_pdf import MarkdownPdf, Section

    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    pdf_obj = MarkdownPdf()

    pdf_obj.add_section(Section(md_content))

    pdf_obj.save(output_file)

    print(f"PDF generated successfully as {output_file}")


def md2html(md_file: str, output_file: str):
    import markdown

    with open(md_file, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    html_output = markdown.markdown(markdown_text)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_output)


if __name__ == "__main__":
    # md2pdf(
    #     "Snowflake_Backup_Recovery_Options.md", "Snowflake_Backup_Recovery_Options.pdf"
    # )

    md2html(
        "Snowflake_Backup_Recovery_Options.md", "Snowflake_Backup_Recovery_Options.html"
    )
