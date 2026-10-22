import pymupdf

doc = pymupdf.open('Final thesis.pdf')
for p in range(72, 80):
    page = doc[p]
    text = doc[p].get_text()
    first_line = text.strip().split('\n')[0] if text.strip() else 'EMPTY'
    img_rects = []
    for img in page.get_images():
        for r in page.get_image_rects(img[0]):
            img_rects.append((round(r.x0,1), round(r.y0,1), round(r.x1,1), round(r.y1,1), round(r.width,1), round(r.height,1)))
    print(f'Page {p+1}: {len(img_rects)} imgs, first line: "{first_line[:40]}"')
    for r in img_rects:
        print(f'   img: x=[{r[0]}, {r[2]}] (w={r[4]}), y=[{r[1]}, {r[3]}] (h={r[5]})')
