// n8n "Code" node (Run Once for All Items), placed between "Any New Gaps?" (true) and "Send Email".
const data = $input.first().json;
const esc = s => String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

const rows = data.groups.map((g, i) => `
  <tr>
    <td>${i + 1}</td>
    <td dir="auto"><b>${esc(g.representative)}</b>
      ${g.variants.length > 1
        ? '<br><small>' + g.variants.slice(1).map(v => '• ' + esc(v)).join('<br>') + '</small>'
        : ''}
    </td>
    <td style="text-align:center">${g.total_asked}</td>
    <td>${esc(g.last_asked)}</td>
  </tr>`).join('');

const html = `
  <p>${data.count} unanswered question group(s), most-asked first.
     Add a verified answer via <code>src/add_faq.py</code> or <code>data/seed.py</code>.</p>
  <table border="1" cellpadding="6" style="border-collapse:collapse">
    <tr><th>#</th><th>Question (and similar phrasings)</th><th>Times asked</th><th>Last asked</th></tr>
    ${rows}
  </table>`;

return [{ json: { subject: `APC: ${data.count} unanswered question group(s)`, html } }];
