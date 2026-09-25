const data = $input.first().json;
const esc = s => String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const cut = (s, n) => (s.length > n ? s.slice(0, n - 1) + '…' : s);

// الموضوع: السؤال الأكثر تكرارًا + عدد المجموعات الباقية
const top = data.groups[0];
const more = data.count > 1 ? ` (+${data.count - 1} أخرى)` : '';
const subject = `أسئلة بلا جواب: "${cut(top.representative, 50)}" ×${top.total_asked}${more}`;

const rows = data.groups.map((g, i) => `
  <tr>
    <td style="text-align:center">${i + 1}</td>
    <td dir="auto"><b>${esc(g.representative)}</b>
      ${g.variants.length > 1
        ? '<br><small>صيغ مشابهة:<br>' + g.variants.slice(1).map(v => '• ' + esc(v)).join('<br>') + '</small>'
        : ''}
    </td>
    <td style="text-align:center">${g.total_asked}</td>
    <td>${esc(g.last_asked)}</td>
  </tr>`).join('');

const html = `
<div dir="rtl" style="font-family:Arial,sans-serif">
  <h2>أسئلة الطلاب التي لم يجد لها المساعد جوابًا</h2>
  <p>عدد المجموعات: <b>${data.count}</b>، مرتبة من الأكثر تكرارًا.
     كل مجموعة تضم الأسئلة المتكررة أو المتشابهة في الصياغة.</p>
  <table border="1" cellpadding="8" style="border-collapse:collapse">
    <tr style="background:#f0f0f0">
      <th>#</th><th>السؤال (وصيغه المشابهة)</th><th>مرات السؤال</th><th>آخر مرة</th>
    </tr>
    ${rows}
  </table>
  <p style="color:#666">لإضافة جواب موثّق: <code>src/add_faq.py</code> أو <code>data/seed.py</code></p>
</div>`;

return [{ json: { subject, html } }];