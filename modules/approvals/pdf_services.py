from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


def build_approval_pdf(document: dict, steps: list[dict]) -> BytesIO:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50

    p.setFont("STSong-Light", 18)
    p.drawString(50, y, "Createx 公文簽核單")
    y -= 35

    p.setFont("STSong-Light", 11)
    lines = [
        f"公文編號：{document.get('doc_no', '')}",
        f"標題：{document.get('title', '')}",
        f"公文類型：{document.get('doc_type', '')}",
        f"申請人：{document.get('applicant_name', '')}",
        f"狀態：{document.get('status', '')}",
        f"目前關卡：{document.get('current_step', '')}",
        f"建立時間：{document.get('created_at', '')}",
    ]

    for line in lines:
        p.drawString(50, y, line)
        y -= 20

    y -= 10
    p.setFont("STSong-Light", 13)
    p.drawString(50, y, "公文內容")
    y -= 22

    p.setFont("STSong-Light", 11)
    content = document.get("content") or ""
    for raw_line in content.splitlines() or [""]:
        wrapped_lines = [raw_line[i:i+45] for i in range(0, len(raw_line), 45)] or [""]
        for line in wrapped_lines:
            p.drawString(50, y, line)
            y -= 18
            if y < 80:
                p.showPage()
                pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
                p.setFont("STSong-Light", 11)
                y = height - 50

    y -= 10
    if y < 120:
        p.showPage()
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        y = height - 50

    p.setFont("STSong-Light", 13)
    p.drawString(50, y, "簽核流程")
    y -= 22

    p.setFont("STSong-Light", 11)
    for step in steps:
        line = (
            f"第 {step.get('step_no', '')} 關｜"
            f"簽核人：{step.get('approver_name', '')}｜"
            f"狀態：{step.get('action_status', '')}｜"
            f"意見：{step.get('action_note', '') or ''}｜"
            f"時間：{step.get('acted_at', '') or ''}"
        )

        chunks = [line[i:i+55] for i in range(0, len(line), 55)] or [""]
        for chunk in chunks:
            p.drawString(50, y, chunk)
            y -= 18
            if y < 60:
                p.showPage()
                pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
                p.setFont("STSong-Light", 11)
                y = height - 50

    p.save()
    buffer.seek(0)
    return buffer