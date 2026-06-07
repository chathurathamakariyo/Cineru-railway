const TelegramBot = require('node-telegram-bot-api');
const axios       = require('axios');
const cheerio     = require('cheerio');
const NodeCache   = require('node-cache');
const crypto      = require('crypto');
const fs          = require('fs');
const path        = require('path');
const os          = require('os');
const PDFDocument = require('pdfkit');
const { createCanvas, loadImage } = require('canvas');
const schedule    = require('node-schedule');
const FormData    = require('form-data');

// ══════════════════════════════════════════════
//  CONFIG
// ══════════════════════════════════════════════
const token        = process.env.BOT_TOKEN || '8301570666:AAHJPDzcFSTS1WWTZicbaj1VgDbUD7ahT7s';
const bot          = new TelegramBot(token, { polling: true });
const CHAI2_API         = 'https://chai2.netlify.app/q?q=';
const IMAGE_GEN_API     = 'https://chimg.vercel.app/gen?q=';
const EDUCATIONAL_AI_API = 'https://psai-pi.vercel.app/';
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || '';
const ADMIN_GROUP  = -1003864845637;

const REQUIRED_CHANNELS = [
  { id: -1003772311516, link: 'https://t.me/SL_pastpaper_updates',  label: '📢 Updates Channel' },
  { id: -1003823507861, link: 'https://t.me/SL_pastpaper_support',  label: '💬 Support Group'   }
];

const AD_URL      = 'https://www.effectivegatecpm.com/fbky7rhgx8?key=97cdfbda8eab8a560f34f30bbb4880c7';
const AD_DELAY_MS = 10000;

// ══════════════════════════════════════════════
//  SRI LANKA TIME HELPERS
// ══════════════════════════════════════════════
const SL_OFFSET_MS = 5.5 * 60 * 60 * 1000;
function nowSL() { return new Date(Date.now() + SL_OFFSET_MS); }
function slDateStr(d) { const sl = new Date(d.getTime() + SL_OFFSET_MS); return sl.toISOString().slice(0, 10); }
function slTimeStr(d) { const sl = new Date(d.getTime() + SL_OFFSET_MS); return sl.toISOString().slice(11, 16) + ' (SLT)'; }

// ══════════════════════════════════════════════
//  SEND HELPERS  (single definition)
// ══════════════════════════════════════════════
function sid(str) { return crypto.createHash('md5').update(String(str)).digest('hex').slice(0, 8); }

function esc(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// kb can be { inline_keyboard: [...] } OR bare array — both handled
async function sendMsg(chatId, html, kb) {
  let markup = null;
  if (kb) {
    markup = Array.isArray(kb) ? { inline_keyboard: kb } : kb;
  }
  const opts = Object.assign({ parse_mode: 'HTML' }, markup ? { reply_markup: markup } : {});
  return bot.sendMessage(chatId, html, opts);
}

async function safeDelete(chatId, msgId) { try { await bot.deleteMessage(chatId, msgId); } catch (_) {} }

async function sendPhoto(chatId, photo, html, kb) {
  const opts = Object.assign({ parse_mode: 'HTML' }, kb ? { reply_markup: kb } : {});
  try { return await bot.sendPhoto(chatId, photo, Object.assign({ caption: html }, opts)); }
  catch (_) { return await bot.sendMessage(chatId, html, opts); }
}

async function editMsg(chatId, msgId, photo, html, kb) {
  try {
    return await bot.editMessageMedia(
      { type: 'photo', media: photo, caption: html, parse_mode: 'HTML' },
      { chat_id: chatId, message_id: msgId, reply_markup: kb }
    );
  } catch (_) {
    try { return await bot.editMessageText(html, { chat_id: chatId, message_id: msgId, parse_mode: 'HTML', reply_markup: kb }); }
    catch (_2) { return await sendPhoto(chatId, photo, html, kb); }
  }
}

// ══════════════════════════════════════════════
//  E-THAKSALAWA CONFIG
// ══════════════════════════════════════════════
const ETH_BASE = 'https://e-thaksalawa.moe.gov.lk/lcms';
const ETH_COURSES = {
  pastpapers:  { label: 'A/L Past Papers',       emoji: '📝', url: ETH_BASE + '/course/view.php?id=45' },
  modelpapers: { label: 'A/L Model Papers',      emoji: '📘', url: ETH_BASE + '/course/view.php?id=46' },
  provincial:  { label: 'A/L Provincial Papers', emoji: '🏫', url: ETH_BASE + '/course/view.php?id=47' }
};
const ETH_UA  = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36';
const ethCache = { categories: new Map(), papers: new Map(), pdfs: new Map() };
const ETH_TTL  = 30 * 60 * 1000;

// ══════════════════════════════════════════════
//  CACHES & SESSION
// ══════════════════════════════════════════════
const searchCache  = new NodeCache({ stdTTL: 60,  checkperiod: 120 });
const resultCache  = new NodeCache({ stdTTL: 300, checkperiod: 360 });
const yearCache    = new NodeCache({ stdTTL: 300, checkperiod: 360 });
const userSessions = new Map();

// ══════════════════════════════════════════════
//  DIRECTORIES & FILES
// ══════════════════════════════════════════════
const DATA_DIR        = path.join(__dirname, 'data');
const COUNTDOWN_DIR   = path.join(DATA_DIR, 'countdown');
const USERS_FILE      = path.join(DATA_DIR, 'users.json');
const SESSIONS_FILE   = path.join(DATA_DIR, 'sessions.json');
const GROUP_CHAT_FILE = path.join(DATA_DIR, 'groupchats.json');

for (const d of [DATA_DIR, COUNTDOWN_DIR]) {
  if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
}

let usersDB = {};
try { usersDB = JSON.parse(fs.readFileSync(USERS_FILE, 'utf8')); } catch (_) {}
function saveUsers() { try { fs.writeFileSync(USERS_FILE, JSON.stringify(usersDB, null, 2)); } catch (_) {} }
function registerUser(from) {
  if (!from) return false;
  const id = String(from.id), isNew = !usersDB[id];
  usersDB[id] = { chatId: from.id, firstName: from.first_name || '', lastName: from.last_name || '', username: from.username || '', joinedAt: usersDB[id] ? usersDB[id].joinedAt : new Date().toISOString() };
  saveUsers(); return isNew;
}
function getAllUserIds() { return Object.values(usersDB).map(u => u.chatId); }

let groupChatsDB = {};
try { groupChatsDB = JSON.parse(fs.readFileSync(GROUP_CHAT_FILE, 'utf8')); } catch (_) {}
function saveGroupChats() { try { fs.writeFileSync(GROUP_CHAT_FILE, JSON.stringify(groupChatsDB, null, 2)); } catch (_) {} }

let sessionsDB = {};
try { sessionsDB = JSON.parse(fs.readFileSync(SESSIONS_FILE, 'utf8')); } catch (_) {}
function saveSessions() { try { fs.writeFileSync(SESSIONS_FILE, JSON.stringify(sessionsDB, null, 2)); } catch (_) {} }
function updSess(chatId, obj) {
  const id = String(chatId);
  userSessions.set(chatId, Object.assign({}, userSessions.get(chatId) || {}, obj));
  sessionsDB[id] = Object.assign({}, sessionsDB[id] || {}, obj);
  saveSessions();
}
function getSess(chatId) {
  if (!userSessions.has(chatId)) { const saved = sessionsDB[String(chatId)] || {}; userSessions.set(chatId, saved); }
  return userSessions.get(chatId) || {};
}

// ══════════════════════════════════════════════
//  IMAGES & EXAM DATES
// ══════════════════════════════════════════════
const BOT_IMG       = 'https://files.catbox.moe/ne3rqr.jpg';
const CD_BG         = 'https://files.catbox.moe/x962h8.jpg';
const PDF_THUMB_URL = 'https://files.catbox.moe/ne3rqr.jpg';
let   PDF_THUMB_BUF = null;

const EXAM_DATES = {
  '2026': new Date('2026-08-11T00:00:00+05:30'),
  '2027': new Date('2027-08-12T00:00:00+05:30')
};
const jobs = {};

// ══════════════════════════════════════════════
//  THEME
// ══════════════════════════════════════════════
function box(title, content) {
  const header    = '🎓 <b>SL_pastpaper_bot</b>  |  <blockquote><i>Sri Lanka A/L Education Hub</i></blockquote>';
  const divider   = '▎';
  const heading   = '▎  📌 <b>' + esc(title) + '</b>';
  const bodyLines = content.split('\n').map(l => '▎  ' + l).join('\n');
  const footer    = '\n<blockquote>✦ <b>PREPARE SMART · SCORE HIGH</b> ✦  |  <i>Powered by SL_pastpaper_bot</i></blockquote>';
  return [header, divider, heading, divider, bodyLines, footer].join('\n');
}

function pdfCaption(title, lines) {
  const rows = lines.map(l => { if (typeof l === 'string') return '▎  ' + l; return '▎  ' + l.label + '  <b>' + esc(String(l.value)) + '</b>'; }).join('\n');
  return '▎  📄 <b>' + esc(title) + '</b>\n▎\n' + rows + '\n▎';
}

// ══════════════════════════════════════════════
//  JOIN CHECK
// ══════════════════════════════════════════════
async function checkUserJoined(userId) {
  const results = [];
  for (const ch of REQUIRED_CHANNELS) {
    try { const m = await bot.getChatMember(ch.id, userId); const joined = ['member','administrator','creator'].includes(m.status); results.push({ ...ch, joined }); }
    catch (_) { results.push({ ...ch, joined: false }); }
  }
  return results;
}

// ══════════════════════════════════════════════
//  KEYBOARDS
// ══════════════════════════════════════════════
function kbMain() {
  return { inline_keyboard: [
    [{ text: '🔍 Search Papers', callback_data: 'search_papers' }, { text: '❓ Help', callback_data: 'help' }],
    [{ text: '🏫 E-Thaksalawa',  callback_data: 'eth_menu' }],
    [{ text: '⏰ Countdown',      callback_data: 'countdown_init' }],
    [{ text: '💬 Support Group', url: 'https://t.me/SL_pastpaper_support' }, { text: '📖 Tutorial', callback_data: 'tutorial' }],
    [{ text: '📢 Channel', url: 'https://t.me/SL_pastpaper_updates' }, { text: '👨‍💻 Owner', url: 'https://chathuradev.netlify.app' }]
  ]};
}
function kbSearch() {
  return { inline_keyboard: [
    [{ text: '📊 Wiki Search', callback_data: 'wiki_search' }, { text: '🏛️ Government Papers', callback_data: 'government_search' }],
    [{ text: '💾 Digital Archives', callback_data: 'digital_search' }],
    [{ text: '🔙 Back', callback_data: 'main_menu' }]
  ]};
}
function kbHelp() {
  return { inline_keyboard: [
    [{ text: '📊 /wiki', callback_data: 'help_wiki' }, { text: '💾 /di', callback_data: 'help_di' }],
    [{ text: '📚 /pp',   callback_data: 'help_pp'   }, { text: '📋 /ps', callback_data: 'help_ps' }],
    [{ text: '🤖 /ai',   callback_data: 'help_ai'   }, { text: '📝 /note', callback_data: 'help_note' }],
    [{ text: '⏰ /countdown', callback_data: 'help_countdown' }, { text: '🏫 /eth', callback_data: 'help_eth' }],
    [{ text: '🔙 Back', callback_data: 'main_menu' }]
  ]};
}
function kbBack(dest) { return { inline_keyboard: [[{ text: '🔙 Back', callback_data: dest || 'main_menu' }]] }; }
function kbTutorial() {
  return { inline_keyboard: [
    [{ text: '🔍 How to Search', callback_data: 'tut_search' }, { text: '🏫 E-Thaksalawa', callback_data: 'tut_eth' }],
    [{ text: '🤖 AI Assistant',  callback_data: 'tut_ai'     }, { text: '📝 Upload Notes', callback_data: 'tut_notes' }],
    [{ text: '⏰ Countdown',      callback_data: 'tut_countdown' }, { text: '📡 Broadcast', callback_data: 'tut_bc' }],
    [{ text: '🔙 Back', callback_data: 'main_menu' }]
  ]};
}
function kbSource(subject) {
  return { inline_keyboard: [
    [{ text: '📊 Wiki', callback_data: 'ps_wiki_' + subject }, { text: '🏛️ Government', callback_data: 'ps_government_' + subject }],
    [{ text: '💾 Digital', callback_data: 'ps_digital_' + subject }],
    [{ text: '🔙 Back', callback_data: 'main_menu' }]
  ]};
}
function kbPagination(cur, total, type, query) {
  const row = [];
  if (cur > 1)     row.push({ text: '◀️ Prev', callback_data: 'page_' + type + '_' + query + '_' + (cur - 1) });
  if (cur < total) row.push({ text: 'Next ▶️', callback_data: 'page_' + type + '_' + query + '_' + (cur + 1) });
  const kb = [];
  if (row.length) kb.push(row);
  kb.push([{ text: '🏠 Main Menu', callback_data: 'main_menu' }]);
  return { inline_keyboard: kb };
}
function kbNoteCtrl() {
  return { inline_keyboard: [
    [{ text: '✅ Enable Auto-Send', callback_data: 'note_enable' }, { text: '❌ Disable Auto-Send', callback_data: 'note_disable' }],
    [{ text: '🔙 Back', callback_data: 'main_menu' }]
  ]};
}
function kbAICtrl() {
  return { inline_keyboard: [
    [{ text: '🎓 Educational AI',      callback_data: 'ai_mode_educational' }],
    [{ text: '🤖 Bot/User AI (chai2)', callback_data: 'ai_mode_user' }],
    [{ text: '❌ Disable AI',          callback_data: 'ai_disable' }],
    [{ text: '🔙 Back', callback_data: 'main_menu' }]
  ]};
}
function kbCountdownYears() {
  return { inline_keyboard: [
    [{ text: '📅 2026 A/L', callback_data: 'countdown_year_2026' }, { text: '📅 2027 A/L', callback_data: 'countdown_year_2027' }],
    [{ text: '🔙 Back', callback_data: 'main_menu' }]
  ]};
}
function kbCountdownCtrl() {
  return { inline_keyboard: [
    [{ text: '✅ Enable Daily', callback_data: 'countdown_enable'  }, { text: '❌ Disable Daily', callback_data: 'countdown_disable' }],
    [{ text: '🔄 Reset',        callback_data: 'countdown_reset'   }, { text: '📅 Change Year',  callback_data: 'countdown_init'    }],
    [{ text: '🔙 Back', callback_data: 'main_menu' }]
  ]};
}
function kbEthMenu() {
  return { inline_keyboard: [
    [{ text: '📝 A/L Past Papers',       callback_data: 'eth_type_pastpapers'  }],
    [{ text: '📘 A/L Model Papers',      callback_data: 'eth_type_modelpapers' }],
    [{ text: '🏫 A/L Provincial Papers', callback_data: 'eth_type_provincial'  }],
    [{ text: '🔙 Back',                  callback_data: 'main_menu'            }]
  ]};
}

// ══════════════════════════════════════════════
//  CATBOX UPLOAD
// ══════════════════════════════════════════════
async function uploadToCatbox(fileBuffer, filename) {
  const form = new FormData();
  form.append('fileToUpload', fileBuffer, filename);
  form.append('reqtype', 'fileupload');
  const res = await axios.post('https://catbox.moe/user/api.php', form, { headers: form.getHeaders(), timeout: 60000 });
  if (!res.data || !res.data.startsWith('https://')) throw new Error('Catbox upload failed');
  return res.data.trim();
}

// ══════════════════════════════════════════════
//  ADMIN NOTIFICATIONS
// ══════════════════════════════════════════════
async function notifyAdminNewUser(from) {
  try {
    const total = Object.keys(usersDB).length;
    const name  = [from.first_name, from.last_name].filter(Boolean).join(' ');
    const uname = from.username ? '@' + from.username : 'N/A';
    await bot.sendMessage(ADMIN_GROUP,
      '🆕 <b>New User Joined!</b>\n━━━━━━━━━━━━━━━━━━━━━\n' +
      '👤 <b>Name:</b> ' + esc(name) + '\n🔗 <b>Username:</b> ' + esc(uname) + '\n' +
      '🆔 <b>Chat ID:</b> <code>' + from.id + '</code>\n' +
      '📅 <b>Joined (SLT):</b> ' + slDateStr(new Date()) + ' ' + slTimeStr(new Date()) + '\n' +
      '👥 <b>Total Users:</b> ' + total,
      { parse_mode: 'HTML' });
  } catch (e) { console.error('[notifyAdmin]', e.message); }
}

async function notifyAdminDownload(from, paperTitle, source) {
  try {
    const name  = from ? [from.first_name, from.last_name].filter(Boolean).join(' ') : 'Unknown';
    const uname = from && from.username ? '@' + from.username : 'N/A';
    const uid   = from ? from.id : 'N/A';
    await bot.sendMessage(ADMIN_GROUP,
      '📥 <b>Paper Downloaded!</b>\n━━━━━━━━━━━━━━━━━━━━━\n' +
      '👤 <b>User:</b> ' + esc(name) + '\n🔗 <b>Username:</b> ' + esc(uname) + '\n' +
      '🆔 <b>Chat ID:</b> <code>' + uid + '</code>\n' +
      '📄 <b>Paper:</b> ' + esc(paperTitle || 'Unknown') + '\n' +
      '🌐 <b>Source:</b> ' + esc(source || 'Unknown') + '\n' +
      '📅 <b>Time (SLT):</b> ' + slDateStr(new Date()) + ' ' + slTimeStr(new Date()),
      { parse_mode: 'HTML' });
  } catch (e) { console.error('[notifyAdminDownload]', e.message); }
}

// ══════════════════════════════════════════════
//  AD + DOWNLOAD FLOW
// ══════════════════════════════════════════════
async function sendAdThenDownload(chatId, downloadFn) {
  const adMsg = await bot.sendMessage(chatId,
    '👆 <b>Click This Ad</b> ↓\n\n⏳ Download starts in <b>5 seconds</b>...\n\n💡 <i>Ad revenue keeps this bot free!</i>',
    { parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: '👆 Click This Ad ← Support Us!', url: AD_URL }]] } }
  );
  await new Promise(r => setTimeout(r, AD_DELAY_MS));
  await safeDelete(chatId, adMsg.message_id);
  await downloadFn();
}

// ══════════════════════════════════════════════
//  EDUCATIONAL AI
// ══════════════════════════════════════════════
async function sendEducationalAI(chatId, question, imageUrl) {
  await bot.sendChatAction(chatId, 'typing');
  const lm = await sendMsg(chatId, '🎓 <b>Educational AI</b> thinking... ⏳');
  try {
    let apiUrl = imageUrl
      ? EDUCATIONAL_AI_API + '?url=' + encodeURIComponent(imageUrl) + '&q=' + encodeURIComponent(question)
      : EDUCATIONAL_AI_API + '?q=' + encodeURIComponent(question);
    const res = await axios.get(apiUrl, { timeout: 30000 });
    await safeDelete(chatId, lm.message_id);
    if (res.data && res.data.answer) {
      const formatted = formatEducationalReply(res.data.answer, imageUrl);
      const chunks    = splitIntoChunks(formatted, 4000);
      for (const chunk of chunks) { await bot.sendMessage(chatId, chunk, { parse_mode: 'HTML' }); await new Promise(r => setTimeout(r, 250)); }
    } else { await sendMsg(chatId, '❌ Educational AI response error. Try again.'); }
  } catch (e) {
    await safeDelete(chatId, lm.message_id);
    console.error('[sendEducationalAI]', e.message);
    await sendMsg(chatId, '❌ <b>Educational AI error:</b> ' + esc(e.message) + '\n\nPlease try again.');
  }
}

function formatEducationalReply(raw, imageUrl) {
  let text = raw.replace(/&(?!amp;|lt;|gt;|quot;|#)/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  text = text.replace(/```([a-zA-Z]*)\n([\s\S]*?)```/g, (_, l, code) => '\n<pre><code>' + code.trim() + '</code></pre>\n');
  text = text.replace(/```([\s\S]*?)```/g, (_, code) => '\n<pre><code>' + code.trim() + '</code></pre>\n');
  text = text.replace(/`([^`\n]+)`/g, (_, i) => '<code>' + i + '</code>');
  text = text.replace(/\*\*([^*\n]+)\*\*/g, '<b>$1</b>');
  text = text.replace(/__([^_\n]+)__/g, '<b>$1</b>');
  text = text.replace(/(?<![*_])\*([^*\n]+)\*(?![*_])/g, '<i>$1</i>');
  text = text.replace(/(?<![_])_([^_\n]+)_(?![_])/g, '<i>$1</i>');
  text = text.replace(/^#{1,2}\s+(.+)$/gm, (_, t) => '\n<blockquote>📌 <b>' + t.trim() + '</b></blockquote>');
  text = text.replace(/^#{3,}\s+(.+)$/gm,  (_, t) => '\n<b>▸ ' + t.trim() + '</b>');
  text = text.replace(/\|\|([^|]+)\|\|/g, '<tg-spoiler>$1</tg-spoiler>');
  const lines = text.split('\n'); const result = []; let inQuote = false, quoteLines = [];
  for (const line of lines) {
    if (/^&gt;\s?/.test(line)) { inQuote = true; quoteLines.push(line.replace(/^&gt;\s?/, '')); }
    else { if (inQuote) { result.push('<blockquote>' + quoteLines.join('\n') + '</blockquote>'); quoteLines = []; inQuote = false; } result.push(line); }
  }
  if (inQuote && quoteLines.length) result.push('<blockquote>' + quoteLines.join('\n') + '</blockquote>');
  text = result.join('\n');
  text = text.replace(/^[\-•]\s+(.+)$/gm, '  ▪️ $1');
  text = text.replace(/^(\d+)\.\s+(.+)$/gm, '<b>$1.</b> $2');
  text = text.replace(/^[-*]{3,}\s*$/gm, '\n━━━━━━━━━━━━━━━━━━\n');
  text = text.replace(/^(📘[^\n]+)$/gm, '<blockquote>$1</blockquote>');
  text = text.replace(/^(📍[^\n]+)$/gm, '<i>$1</i>');
  text = text.replace(/^(✅[^\n]+)$/gm, '<b>$1</b>');
  text = text.replace(/^(💡[^\n]+)$/gm, '<i>$1</i>');
  text = text.replace(/\n{3,}/g, '\n\n');
  const header = imageUrl ? '<blockquote>🖼️ <b>Image Analysis</b>  ·  <a href="' + imageUrl + '">View Image</a></blockquote>\n\n' : '';
  return header + text.trim();
}

function splitIntoChunks(text, maxLen) {
  const chunks = []; let rem = text;
  while (rem.length > maxLen) {
    let cut = rem.lastIndexOf('\n\n', maxLen);
    if (cut < maxLen * 0.5) cut = rem.lastIndexOf('\n', maxLen);
    if (cut < maxLen * 0.3) cut = maxLen;
    chunks.push(rem.slice(0, cut).trim()); rem = rem.slice(cut).trim();
  }
  if (rem.trim()) chunks.push(rem.trim());
  return chunks;
}

// ══════════════════════════════════════════════
//  IMAGE HANDLER FOR EDUCATIONAL AI
// ══════════════════════════════════════════════
async function handleImageForAI(msg) {
  const chatId = msg.chat.id;
  const caption = msg.caption ? msg.caption.trim() : '';
  let imageFileId = null;
  if (msg.photo) imageFileId = msg.photo[msg.photo.length - 1].file_id;
  else if (msg.document && msg.document.mime_type && msg.document.mime_type.startsWith('image/')) imageFileId = msg.document.file_id;
  if (!imageFileId) return;
  const lm = await sendMsg(chatId, '📤 <b>Image upload කරමින්...</b> Please wait ⏳');
  try {
    const fileObj = await bot.getFile(imageFileId);
    const fileUrl = 'https://api.telegram.org/file/bot' + token + '/' + fileObj.file_path;
    const imgRes  = await axios.get(fileUrl, { responseType: 'arraybuffer', timeout: 30000 });
    const imgBuf  = Buffer.from(imgRes.data);
    const ext     = fileObj.file_path.split('.').pop() || 'jpg';
    const catboxUrl = await uploadToCatbox(imgBuf, 'image_' + Date.now() + '.' + ext);
    await safeDelete(chatId, lm.message_id);
    await sendEducationalAI(chatId, caption || 'මේ image eka ගැන explain කරන්න', catboxUrl);
  } catch (e) {
    await safeDelete(chatId, lm.message_id);
    console.error('[handleImageForAI]', e.message);
    await sendMsg(chatId, '❌ <b>Image process කරන්න බැරි වුනා:</b> ' + esc(e.message));
  }
}

// ══════════════════════════════════════════════
//  AI (chai2 / claude fallback)
// ══════════════════════════════════════════════
const AI_SYSTEM_CONTEXT = [
  'Your name is SL_pastpaper_bot and your owner chathura hansaka,his website chathuradev.netlify.app and his telegram chanel @aboutchathura . You are a smart AI assistant for Sri Lanka A/L students.',
  'IDENTITY — answer these exactly:',
  '  Owner/Creator/haduwe kawda: Chathura Hansaka,his telegram chanel @aboutchathura, Website: https://chathuradev.netlify.app',
  '  Support group: https://t.me/SL_pastpaper_support (Telegram — help & updates)',
  '  How to get papers: /wiki <subject>  /di <subject>  /pp <subject>  /ps <subject>',
  '  Example: user says history 2019 paper denna -> reply: type /wiki history 2019 or /pp history then pick 2019 button. Bot downloads and sends the PDF.',
  '  Bot features: A/L past papers, model papers, provincial papers, E-Thaksalawa, AI assistant, note upload, exam countdown.',
  'LANGUAGE RULE: Reply in the SAME language the user writes. Sinhala->Sinhala. English->English. Mixed->mixed.',
  'CODE RULE: For ANY coding request write COMPLETE WORKING code in markdown code blocks with language tag. Explain after.',
  'GENERAL RULE: Answer ANY question. Never refuse.'
].join(' ');

const aiHistories = new Map();
const AI_HISTORY_LIMIT = 10;
function getHistory(chatId) { if (!aiHistories.has(chatId)) aiHistories.set(chatId, []); return aiHistories.get(chatId); }
function addHistory(chatId, role, content) { const h = getHistory(chatId); h.push({ role, content }); if (h.length > AI_HISTORY_LIMIT * 2) h.splice(0, h.length - AI_HISTORY_LIMIT * 2); }
function clearHistory(chatId) { aiHistories.delete(chatId); }

async function askAI(q, chatId) {
  try {
    const shortQ  = q.length > 300 ? q.slice(0, 300) : q;
    const MINI_CTX = 'You are SL_pastpaper_bot for Sri Lanka A/L students by Chathura Hansaka. Owner: Chathura Hansaka (https://chathuradev.netlify.app). Support: https://t.me/SL_pastpaper_support. Papers: /wiki /di /pp /ps. Reply same language as user. Write complete code blocks for code requests.';
    const r = await axios.get(CHAI2_API + encodeURIComponent(MINI_CTX + '\n\nUser: ' + shortQ + '\nAssistant:'), { timeout: 20000 });
    const reply = (r.data && (r.data.response || r.data.text)) || null;
    if (reply && reply.trim()) { if (chatId) { addHistory(chatId, 'user', q); addHistory(chatId, 'assistant', reply); } return reply; }
  } catch (e) { console.warn('[askAI/chai2 failed]', e.message); }

  if (ANTHROPIC_API_KEY) {
    try {
      const messages = [...getHistory(chatId || 0), { role: 'user', content: q }];
      const r = await axios.post('https://api.anthropic.com/v1/messages',
        { model: 'claude-haiku-4-5-20251001', max_tokens: 1500, system: AI_SYSTEM_CONTEXT, messages },
        { headers: { 'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' }, timeout: 30000 }
      );
      const reply = (r.data.content && r.data.content[0] && r.data.content[0].text) || 'No response.';
      if (chatId) { addHistory(chatId, 'user', q); addHistory(chatId, 'assistant', reply); }
      return reply;
    } catch (e) {
      const status = e.response && e.response.status;
      if (status === 401) return '❌ Invalid Claude API key.';
      if (status === 429) return '⏳ AI rate limit hit. Please try again shortly.';
      console.error('[askAI/claude]', e.message);
    }
  }
  return 'AI service is currently unavailable. Please try again later.';
}

const PAPER_NOISE = ['past paper','model paper','provincial paper','paper','papers','exam','question','questions','answers','answer','marking scheme','give me','denna','karanna','eka','ekak','illuwama','illawa','wage','ganna','send','find','get','show','download','meka','me','the','mata','oya','api','mama','kohomada','kohoma'];
function detectPaperRequest(text) {
  const t = text.toLowerCase().trim();
  const paperWords  = ['paper','papers','past paper','exam','question','answers','marking scheme','model paper'];
  const yearMatch   = t.match(/\b(20\d{2}|19\d{2})\b/);
  const hasPaperWord = paperWords.some(w => t.includes(w));
  const subjectYear  = t.match(/^([a-z][a-z\s]{1,30})\s+(20\d{2}|19\d{2})/);
  if (!hasPaperWord && !subjectYear) return null;
  let subject = t.replace(/\b(20\d{2}|19\d{2})\b/g, ' ').replace(/[^a-z\s]/g, ' ');
  for (const noise of PAPER_NOISE) { const re = new RegExp('\\b' + noise.replace(/\s/g, '\\s+') + '\\b', 'gi'); subject = subject.replace(re, ' '); }
  subject = subject.trim().replace(/\s+/g, ' ').trim();
  if (!subject && subjectYear) subject = subjectYear[1].trim();
  if (!subject || subject.length < 2) return null;
  const year = yearMatch ? yearMatch[1] : (subjectYear ? subjectYear[2] : null);
  return { subject, year };
}

const CODE_LANGS = ['python','javascript','java','c++','cpp','c#','php','html','css','sql','kotlin','swift','typescript','ruby','go','rust','bash','shell','nodejs'];
const CODE_WORDS = ['code','program','function','script','example','algorithm','implement','write a','create a'];
function detectCodeRequest(text) {
  const t = text.toLowerCase();
  return CODE_WORDS.some(w => t.includes(w)) || CODE_LANGS.some(l => t.includes(l)) || ['code','ekak denna','ekak liyanna','liyanna','hadanna'].some(w => t.includes(w));
}
function detectImageRequest(text) {
  const t = text.toLowerCase();
  return ['image','picture','photo','draw','generate image','create image','make image','image ekak','diagram','generate','create a picture'].some(w => t.includes(w));
}

async function addWatermark(imageUrl) {
  try {
    const imgRes = await axios.get(imageUrl, { responseType: 'arraybuffer', timeout: 30000 });
    const baseImg = await loadImage(Buffer.from(imgRes.data));
    const W = baseImg.width, H = baseImg.height;
    const canvas = createCanvas(W, H); const ctx = canvas.getContext('2d');
    ctx.drawImage(baseImg, 0, 0, W, H);
    const LOGO_SIZE = Math.round(Math.min(W, H) * 0.07), PADDING = Math.round(LOGO_SIZE * 0.4);
    try { const logo = await loadImage(PDF_THUMB_URL); ctx.save(); ctx.beginPath(); ctx.arc(PADDING + LOGO_SIZE / 2, H - PADDING - LOGO_SIZE / 2, LOGO_SIZE / 2, 0, Math.PI * 2); ctx.clip(); ctx.drawImage(logo, PADDING, H - PADDING - LOGO_SIZE, LOGO_SIZE, LOGO_SIZE); ctx.restore(); } catch (_) {}
    const FONT_SIZE = Math.round(LOGO_SIZE * 0.55), TEXT_X = PADDING + LOGO_SIZE + Math.round(LOGO_SIZE * 0.25), TEXT_Y = H - PADDING - LOGO_SIZE / 2 + FONT_SIZE * 0.35;
    ctx.font = `bold ${FONT_SIZE}px sans-serif`; ctx.textAlign = 'left';
    ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = 6; ctx.shadowOffsetX = 1; ctx.shadowOffsetY = 1;
    const tm = ctx.measureText('@SL_pastpaper_bot'), pillW = tm.width + FONT_SIZE, pillH = FONT_SIZE * 1.6;
    ctx.save(); ctx.shadowColor = 'transparent'; ctx.fillStyle = 'rgba(0,0,0,0.45)';
    ctx.beginPath(); ctx.roundRect(TEXT_X - FONT_SIZE * 0.4, TEXT_Y - FONT_SIZE * 1.1, pillW, pillH, pillH / 2); ctx.fill(); ctx.restore();
    ctx.fillStyle = '#ffffff'; ctx.fillText('@SL_pastpaper_bot', TEXT_X, TEXT_Y); ctx.shadowColor = 'transparent';
    return canvas.toBuffer('image/png');
  } catch (e) { console.error('[watermark]', e.message); return null; }
}

async function sendAIImage(chatId, userRequest) {
  const lm = await sendMsg(chatId, '🎨 <b>Image generate කරමින්...</b> Please wait ⏳');
  let actionAlive = true;
  const actionInterval = setInterval(() => { if (actionAlive) bot.sendChatAction(chatId, 'upload_photo').catch(() => {}); }, 4000);
  try {
    await bot.sendChatAction(chatId, 'upload_photo');
    let imagePrompt = userRequest;
    try {
      const MINI_CTX = 'You are an expert image prompt engineer. Output only the image prompt.';
      const r = await axios.get(CHAI2_API + encodeURIComponent(MINI_CTX + '\n\nUser: Generate a detailed English image generation prompt (max 150 words) for: ' + userRequest + '. Return ONLY the prompt.\nAssistant:'), { timeout: 15000 });
      const aiPrompt = (r.data && (r.data.response || r.data.text)) || null;
      if (aiPrompt && aiPrompt.trim().length > 10) imagePrompt = aiPrompt.trim();
    } catch (_) {}
    if (imagePrompt.length > 500) imagePrompt = imagePrompt.slice(0, 500);
    const res = await axios.get(IMAGE_GEN_API + encodeURIComponent(imagePrompt), { timeout: 90000 });
    if (!res.data || !res.data.result) throw new Error('Image generation failed — no result');
    actionAlive = false; clearInterval(actionInterval);
    await safeDelete(chatId, lm.message_id);
    const wmBuf = await addWatermark(res.data.result);
    if (wmBuf) {
      const tmpPath = path.join(os.tmpdir(), 'img_wm_' + chatId + '_' + Date.now() + '.png');
      fs.writeFileSync(tmpPath, wmBuf);
      await bot.sendPhoto(chatId, tmpPath, { caption: '🎨 <b>Generated Image</b>\n\n<i>' + esc(userRequest.slice(0, 120)) + '</i>', parse_mode: 'HTML' });
      try { fs.unlinkSync(tmpPath); } catch (_) {}
    } else {
      await bot.sendPhoto(chatId, res.data.result, { caption: '🎨 <b>Generated Image</b>\n\n<i>' + esc(userRequest.slice(0, 120)) + '</i>', parse_mode: 'HTML' });
    }
  } catch (e) {
    actionAlive = false; clearInterval(actionInterval);
    await safeDelete(chatId, lm.message_id);
    await bot.sendMessage(chatId, '❌ <b>Image generate කරන්න බැරි වුනා.</b>\n\n<i>' + esc(e.message) + '</i>', { parse_mode: 'HTML' });
  }
}

function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function formatAIReply(raw) {
  let out = raw;
  const FENCE = String.fromCharCode(96,96,96);
  out = out.replace(new RegExp(FENCE + '([a-zA-Z]*)\\n([\\s\\S]*?)' + FENCE, 'g'), (_, l, code) => '\n<pre><code>' + escHtml(code.trim()) + '</code></pre>\n');
  const BT = String.fromCharCode(96);
  out = out.replace(new RegExp(BT + '([^' + BT + '\\n]+)' + BT, 'g'), (_, i) => '<code>' + escHtml(i) + '</code>');
  out = out.replace(/^#{1,3}\s+(.+)$/gm, '<b>$1</b>');
  out = out.replace(/\*\*([^*\n]+)\*\*/g, '<b>$1</b>');
  out = out.replace(/&(?!amp;|lt;|gt;|quot;)/g, '&amp;');
  return out;
}

async function sendAI(chatId, question) {
  await bot.sendChatAction(chatId, 'typing');
  if (detectImageRequest(question)) { await sendAIImage(chatId, question); return; }
  const paperReq = detectPaperRequest(question);
  if (paperReq && paperReq.subject) {
    const subj = paperReq.subject, yearTxt = paperReq.year ? ' ' + paperReq.year : '';
    await sendPhoto(chatId, BOT_IMG, box('Paper Found!', '📄 <b>' + esc(subj + yearTxt) + '</b> paper search කරමු!\n\nSource select කරන්න 👇'),
      { inline_keyboard: [[{ text: '📊 Wiki', callback_data: 'ps_wiki_' + subj + yearTxt }],[{ text: '💾 Digital', callback_data: 'ps_digital_' + subj + yearTxt }],[{ text: '🏛️ Government', callback_data: 'ps_government_' + subj + yearTxt }],[{ text: '🏠 Main Menu', callback_data: 'main_menu' }]] });
    return;
  }
  const rawReply = await askAI(question, chatId);
  await new Promise(r => setTimeout(r, Math.min(2000, Math.max(400, rawReply.length * 8))));
  const FENCE3 = String.fromCharCode(96,96,96);
  if (detectCodeRequest(question) || rawReply.includes(FENCE3)) {
    const formatted = formatAIReply(rawReply); const chunks = []; let rem = formatted;
    while (rem.length > 3800) { let cut = rem.lastIndexOf('\n', 3800); if (cut < 500) cut = 3800; chunks.push(rem.slice(0, cut)); rem = rem.slice(cut); }
    if (rem.trim()) chunks.push(rem);
    for (const chunk of chunks) { await bot.sendMessage(chatId, chunk, { parse_mode: 'HTML' }); await new Promise(r => setTimeout(r, 200)); }
    return;
  }
  await sendMsg(chatId, esc(rawReply));
}

// ══════════════════════════════════════════════
//  E-THAKSALAWA SCRAPERS
// ══════════════════════════════════════════════
async function ethPage(url) {
  try { const r = await axios.get(url, { headers: { 'User-Agent': ETH_UA, Accept: 'text/html,*/*' }, timeout: 10000, maxRedirects: 5 }); return cheerio.load(r.data); }
  catch (e) { console.error('[ethPage]', e.message); return null; }
}
async function ethPdf(resourceUrl) {
  if (ethCache.pdfs.has(resourceUrl)) return ethCache.pdfs.get(resourceUrl);
  try {
    const $ = await ethPage(resourceUrl); if (!$) { ethCache.pdfs.set(resourceUrl, null); return null; }
    let pdfUrl = null;
    $('a').each((_, el) => { const h = $(el).attr('href'); if (h && h.toLowerCase().includes('.pdf')) pdfUrl = h.startsWith('http') ? h : ETH_BASE + h; });
    if (!pdfUrl) $('object,embed').each((_, el) => { const d = $(el).attr('data') || $(el).attr('src'); if (d && d.includes('.pdf')) pdfUrl = d.startsWith('http') ? d : ETH_BASE + d; });
    ethCache.pdfs.set(resourceUrl, pdfUrl); return pdfUrl;
  } catch (e) { ethCache.pdfs.set(resourceUrl, null); return null; }
}
async function ethCats(type) {
  const c = ethCache.categories.get(type);
  if (c && Date.now() - c.ts < ETH_TTL) return c.data;
  const course = ETH_COURSES[type]; if (!course) return null;
  try {
    const $ = await ethPage(course.url); if (!$) return null;
    const cats = [];
    $('li.section').each((_, s) => { const h = $(s).find('h3').first().text().trim().replace(/\s+/g, ' '); if (h && h !== 'General' && !h.includes('Announcements') && !cats.includes(h)) cats.push(h); });
    cats.sort(); ethCache.categories.set(type, { data: cats, ts: Date.now() }); return cats;
  } catch (_) { return null; }
}
async function ethPapers(type, category) {
  const key = type + '|' + category, c = ethCache.papers.get(key);
  if (c && Date.now() - c.ts < ETH_TTL) return c.data;
  const course = ETH_COURSES[type]; if (!course) return null;
  try {
    const $ = await ethPage(course.url); if (!$) return null;
    const papers = [];
    $('li.section').each((_, s) => {
      const h = $(s).find('h3').first().text().trim().replace(/\s+/g, ' ');
      if (h === category) { $(s).find("a[href*='mod/resource/view.php']").each((_, el) => { const name = $(el).text().trim().replace(/\s+File\s*$/i,'').replace(/\s+/g,' '); let url = $(el).attr('href'); if (url && !url.startsWith('http')) url = ETH_BASE + (url.startsWith('/') ? url : '/' + url); if (name && url) papers.push({ name, resource_url: url, pdf_url: null }); }); }
    });
    if (!papers.length) return null;
    for (let i = 0; i < papers.length; i += 5) { await Promise.all(papers.slice(i, i+5).map(async p => { p.pdf_url = await ethPdf(p.resource_url); await new Promise(r => setTimeout(r, 80)); })); }
    ethCache.papers.set(key, { data: papers, ts: Date.now() }); return papers;
  } catch (_) { return null; }
}

// ══════════════════════════════════════════════
//  GROUP CHAT ON / OFF
// ══════════════════════════════════════════════
bot.onText(/^\/chat\s+on$/i, async msg => {
  const chatId = msg.chat.id, chatType = msg.chat.type;
  if (chatType !== 'group' && chatType !== 'supergroup') return sendMsg(chatId, '⚠️ මෙම command group chats සරු පමණි.');
  groupChatsDB[String(chatId)] = true; saveGroupChats();
  await bot.sendMessage(chatId, '✅ <b>Chat mode enabled!</b>\n\nදැන් මෙම group ට bot respond කරනවා.\nDisable: <code>/chat off</code>\n\n📋 <b>Commands:</b>\n<code>/wiki</code> <code>/di</code> <code>/pp</code> <code>/ps</code> <code>/eth</code> <code>/ai</code> <code>/aicontrol</code> <code>/countdown</code>', { parse_mode: 'HTML' });
});
bot.onText(/^\/chat\s+off$/i, async msg => {
  const chatId = msg.chat.id, chatType = msg.chat.type;
  if (chatType !== 'group' && chatType !== 'supergroup') return sendMsg(chatId, '⚠️ මෙම command group chats සරු පමණි.');
  delete groupChatsDB[String(chatId)]; saveGroupChats();
  await bot.sendMessage(chatId, '❌ <b>Chat mode disabled!</b>\n\nEnable: <code>/chat on</code>', { parse_mode: 'HTML' });
});

function isChatAllowed(msg) {
  const t = msg.chat.type;
  if (t === 'private') return true;
  if (t === 'group' || t === 'supergroup') return !!groupChatsDB[String(msg.chat.id)];
  return false;
}

// ══════════════════════════════════════════════
//  STICKER + WELCOME
// ══════════════════════════════════════════════
let CACHED_STICKER_ID = null;
async function sendWelcomeSticker(chatId) {
  if (CACHED_STICKER_ID) { try { await bot.sendSticker(chatId, CACHED_STICKER_ID); return true; } catch (_) { CACHED_STICKER_ID = null; } }
  try { const fwd = await bot.forwardMessage(chatId, -1003864845637, 2); if (fwd && fwd.sticker) CACHED_STICKER_ID = fwd.sticker.file_id; return true; } catch (_) {}
  try { await bot.forwardMessage(chatId, '@jdkfkgkoeke', 2); return true; } catch (_) {}
  return false;
}

async function showWelcome(chatId, name) {
  await sendPhoto(chatId, BOT_IMG, box('Welcome to SL PastPaper Bot!',
    '🎉 <b>Hello ' + name + '!</b>\n\n📚 Your complete A/L Past Paper companion for Sri Lanka!\n\n' +
    '⚡ <b>What I can do:</b>\n  › 📊 Wiki / Gov / Digital paper search\n  › 🏫 E-Thaksalawa official papers\n' +
    '  › 🤖 AI answers with typing effect\n  › 📝 Note upload &amp; auto-send\n  › ⏰ Exam countdown timer\n\nChoose an option below! 👇'
  ), kbMain());
}

async function handleStartParam(chatId, from, name, param) {
  if (param && param.startsWith('dl_')) {
    const dlId = param.replace('dl_', ''), cached = resultCache.get(dlId);
    if (cached) {
      await showWelcome(chatId, name);
      await new Promise(r => setTimeout(r, 800));
      await sendAdThenDownload(chatId, async () => {
        const lm = await sendMsg(chatId, '📥 Downloading <b>' + esc(cached.title) + '</b>...');
        try {
          const links = (cached.allLinks && cached.allLinks.length) ? cached.allLinks : [cached.url];
          let buf = null, lastErr = null;
          for (const link of links) { try { const r = await downloadAnyPdf(link); buf = r.buf; break; } catch (e) { lastErr = e; } }
          if (!buf) throw lastErr || new Error('All download links failed');
          await safeDelete(chatId, lm.message_id);
          const safeTitle = String(cached.title || 'SL_pastpaper_bot').replace(/[/\\:*?"<>|]/g,'_').replace(/\s+/g,' ').trim().slice(0,100);
          const srcLabel  = String(cached.source||'').charAt(0).toUpperCase() + String(cached.source||'').slice(1);
          await bot.sendDocument(chatId, buf, { filename: safeTitle + '.pdf', caption: pdfCaption(cached.title, [{ label:'📦 Size   :', value:(buf.length/1048576).toFixed(2)+' MB'},{label:'🌐 Source :',value:srcLabel},'─────────────────────','🎓  Good luck with your studies!']), parse_mode:'HTML' });
          if (from) await notifyAdminDownload(from, cached.title, srcLabel);
        } catch (e) { await safeDelete(chatId, lm.message_id); await sendMsg(chatId, '❌ <b>Download failed:</b> ' + esc(e.message)); }
      });
      return;
    }
  }
  await showWelcome(chatId, name);
}

// ══════════════════════════════════════════════
//  /start
// ══════════════════════════════════════════════
bot.onText(/\/start(?:\s+(.+))?/, async msg => {
  if (msg.chat.type !== 'private') return;
  const chatId = msg.chat.id, from = msg.from;
  const param  = (msg.text || '').replace('/start','').trim();
  const name   = esc(from.first_name || 'Student');
  const isNew  = registerUser(from);
  if (isNew) await notifyAdminNewUser(from);
  await sendWelcomeSticker(chatId).catch(() => {});
  const channelStatus = await checkUserJoined(from.id);
  const notJoined     = channelStatus.filter(c => !c.joined);
  if (notJoined.length > 0) {
    if (param) updSess(chatId, { pendingStartParam: param });
    await sendPhoto(chatId, BOT_IMG, box('Join Required! 🔒',
      '👋 <b>Hello ' + name + '!</b>\n\n⚠️ Bot use කරන්නට පළමුව join කරන්න:\n\n' +
      notJoined.map(ch => '  ➡️ ' + ch.label).join('\n') + '\n\nJoin කරලා <b>"✅ ඔව් Join කළා"</b> click කරන්න.'
    ), { inline_keyboard: [...notJoined.map(ch => [{ text: ch.label + ' — Join Now', url: ch.link }]), [{ text: '✅ ඔව් Join කළා — Check', callback_data: 'check_join' }]] });
    return;
  }
  await handleStartParam(chatId, from, name, param);
});

// ══════════════════════════════════════════════
//  INLINE QUERY
// ══════════════════════════════════════════════
bot.on('inline_query', async (query) => {
  const text = (query.query || '').trim();
  if (!text || text.length < 2) {
    return bot.answerInlineQuery(query.id, [{ type:'article', id:'hint', title:'🔍 Type subject name to search...', description:'Example: sinhala 2024', input_message_content:{ message_text:'📚 Use @SL_pastpaper_bot [subject] to search papers' } }], { cache_time:10 });
  }
  try {
    const res  = await axios.get('https://chwiki.netlify.app/?q=' + encodeURIComponent(text), { timeout: 8000 });
    const data = res.data;
    if (!data.status || !data.results || !data.results.length) {
      return bot.answerInlineQuery(query.id, [{ type:'article', id:'noresult', title:'❌ No papers found for: '+text, description:'Try a different subject name', input_message_content:{ message_text:'❌ No papers found for "'+text+'"\n\nTry: /wiki '+text } }], { cache_time:30 });
    }
    const validResults = data.results.filter(r => r.pdfLinks && r.pdfLinks.length > 0);
    const inlineResults = validResults.slice(0, 10).map((r, i) => {
      const primaryLink = r.pdfLinks[0];
      const id = sid(primaryLink + '||' + (r.title || ''));
      resultCache.set(id, { url: primaryLink, allLinks: r.pdfLinks, title: r.title || 'Paper', source: 'wiki' });
      const title = r.title || 'Paper ' + (i + 1);
      return { type:'article', id:'paper_'+id, title:'📄 '+title.slice(0,80), description:'🌐 Wiki | Tap to send download button',
        input_message_content:{ message_text:'📄 <b>'+esc(title)+'</b>\n\n🔍 Found via <b>@SL_pastpaper_bot</b>\n\n📥 <b>Click below to download:</b>', parse_mode:'HTML' },
        reply_markup:{ inline_keyboard:[[{ text:'📥 Download Paper', url:'https://t.me/SL_pastpaper_bot?start=dl_'+id }]] } };
    });
    await bot.answerInlineQuery(query.id, inlineResults, { cache_time:60 });
  } catch (e) {
    console.error('[inline_query]', e.message);
    await bot.answerInlineQuery(query.id, [{ type:'article', id:'error', title:'⚠️ Search error. Try again.', description:e.message, input_message_content:{ message_text:'⚠️ Search failed. Use /wiki '+text+' directly.' } }], { cache_time:5 });
  }
});

// ══════════════════════════════════════════════
//  MESSAGE HANDLER
// ══════════════════════════════════════════════
bot.on('message', async msg => {
  // Admin group commands
  if (msg.chat.id === ADMIN_GROUP) {
    if (msg.text && msg.text.startsWith('/bc')) { await handleBroadcast(msg); return; }
    if (msg.caption && msg.caption.startsWith('/bc')) { await handleBroadcast(msg); return; }
    if (msg.text && msg.text.trim() === '/stats') { await handleStats(msg); return; }
  }

  const chatId    = msg.chat.id, chatType = msg.chat.type;
  const isGroup   = chatType === 'group' || chatType === 'supergroup';
  const isPrivate = chatType === 'private';
  const groupOn   = isGroup && !!groupChatsDB[String(chatId)];

  if (msg.from) { const isNew = registerUser(msg.from); if (isNew && isPrivate) await notifyAdminNewUser(msg.from); }
  if (!isPrivate && !groupOn) return;

  const msgText = msg.text && msg.text.trim();
  if (msgText && msgText.startsWith('/')) return;

  // Image handler
  if (isPrivate && (msg.photo || (msg.document && msg.document.mime_type && msg.document.mime_type.startsWith('image/')))) {
    const sess = getSess(chatId);
    if ((sess.aiMode || 'off') === 'educational' || (sess.aiMode || 'off') === 'off') { await handleImageForAI(msg); return; }
  }
  if (!msgText) return;

  const sess = getSess(chatId), aiMode = sess.aiMode || 'off';
  if (aiMode === 'educational') { await sendEducationalAI(chatId, msgText, null); return; }
  if (aiMode === 'user' || sess.aiEnabled) { await sendAI(chatId, msgText); return; }

  if (isPrivate && sess.noteAutoSend !== false) {
    const hits = findNotes(msgText);
    if (hits.length === 1) { await deliverNote(chatId, hits[0]); return; }
    if (hits.length > 1) { const qKey = sid(msgText.toLowerCase()); resultCache.set('noteq_' + qKey, hits, 300); await showNotePage(chatId, qKey, 1, msgText); return; }
  }

  if (sess.waitingForQuery && sess.searchType) {
    updSess(chatId, { waitingForQuery: false });
    const sm = await sendMsg(chatId, '🔍 Searching <b>' + esc(msgText) + '</b>...');
    await doSearch(chatId, msgText, sess.searchType, 1, msg.from);
    await safeDelete(chatId, sm.message_id); return;
  }

  const paperReq = detectPaperRequest(msgText);
  if (paperReq && paperReq.subject) {
    const subj = paperReq.subject, yearTxt = paperReq.year ? ' ' + paperReq.year : '';
    await sendPhoto(chatId, BOT_IMG, box('Paper Found!', '📄 <b>' + esc(subj + yearTxt) + '</b> paper search කරමු!\n\nSource select කරන්න 👇'),
      { inline_keyboard: [[{ text:'📊 Wiki', callback_data:'ps_wiki_'+subj+yearTxt}],[{ text:'💾 Digital', callback_data:'ps_digital_'+subj+yearTxt}],[{ text:'🏛️ Government', callback_data:'ps_government_'+subj+yearTxt}],[{ text:'🏠 Main Menu', callback_data:'main_menu'}]] });
    return;
  }
  if (isGroup) { await sendAI(chatId, msgText); return; }
  await psPrompt(chatId, msgText);
});

// Reply-to-image handler
bot.on('message', async msg => {
  if (msg.chat.type !== 'private' || !msg.reply_to_message || !msg.text) return;
  const replied = msg.reply_to_message;
  if (!replied.photo && !(replied.document && replied.document.mime_type && replied.document.mime_type.startsWith('image/'))) return;
  const chatId = msg.chat.id, question = msg.text.trim();
  if (question.startsWith('/')) return;
  const lm = await sendMsg(chatId, '📤 <b>Image upload කරමින්...</b> Please wait ⏳');
  try {
    const imageFileId = replied.photo ? replied.photo[replied.photo.length-1].file_id : replied.document.file_id;
    const fileObj = await bot.getFile(imageFileId);
    const imgRes  = await axios.get('https://api.telegram.org/file/bot'+token+'/'+fileObj.file_path, { responseType:'arraybuffer', timeout:30000 });
    const catboxUrl = await uploadToCatbox(Buffer.from(imgRes.data), 'img_'+Date.now()+'.'+(fileObj.file_path.split('.').pop()||'jpg'));
    await safeDelete(chatId, lm.message_id);
    await sendEducationalAI(chatId, question, catboxUrl);
  } catch (e) { await safeDelete(chatId, lm.message_id); await sendMsg(chatId, '❌ Image process error: ' + esc(e.message)); }
});

// ══════════════════════════════════════════════
//  ADMIN HANDLERS
// ══════════════════════════════════════════════
async function handleStats(msg) {
  try {
    const totalUsers = Object.keys(usersDB).length, totalGroups = Object.keys(groupChatsDB).length;
    let cdCount = 0;
    try { cdCount = fs.readdirSync(COUNTDOWN_DIR).filter(f => f.endsWith('.json')).length; } catch (_) {}
    const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
    const recentUsers = Object.values(usersDB).filter(u => { try { return new Date(u.joinedAt).getTime() > weekAgo; } catch (_) { return false; } }).length;
    await bot.sendMessage(ADMIN_GROUP,
      '📊 <b>Bot Statistics</b>\n━━━━━━━━━━━━━━━━━━━━━\n' +
      '👥 <b>Total Users:</b> ' + totalUsers + '\n🆕 <b>New (last 7 days):</b> ' + recentUsers + '\n' +
      '🏘️ <b>Active Groups:</b> ' + totalGroups + '\n⏰ <b>Countdown Users:</b> ' + cdCount + '\n' +
      '📅 <b>Time (SLT):</b> ' + slDateStr(new Date()) + ' ' + slTimeStr(new Date()),
      { parse_mode: 'HTML' });
  } catch (e) { await bot.sendMessage(ADMIN_GROUP, '❌ Stats error: ' + e.message, { parse_mode: 'HTML' }); }
}

async function handleBroadcast(msg) {
  const adminChatId = msg.chat.id, userIds = getAllUserIds();
  if (!userIds.length) { await sendMsg(adminChatId, '⚠️ No users registered yet.'); return; }
  const rawCaption = (msg.caption || msg.text || '').replace(/^\/bc\s*/i, '').trim();
  let ok = 0, fail = 0;
  const sm = await bot.sendMessage(adminChatId, '📡 Broadcasting to <b>' + userIds.length + '</b> users...', { parse_mode: 'HTML' });
  for (const uid of userIds) {
    try {
      if (msg.photo) await bot.sendPhoto(uid, msg.photo[msg.photo.length-1].file_id, rawCaption ? { caption:rawCaption, parse_mode:'HTML' } : {});
      else if (msg.video) await bot.sendVideo(uid, msg.video.file_id, rawCaption ? { caption:rawCaption, parse_mode:'HTML' } : {});
      else if (msg.audio) await bot.sendAudio(uid, msg.audio.file_id, rawCaption ? { caption:rawCaption, parse_mode:'HTML' } : {});
      else if (msg.document) await bot.sendDocument(uid, msg.document.file_id, rawCaption ? { caption:rawCaption, parse_mode:'HTML' } : {});
      else if (msg.voice) await bot.sendVoice(uid, msg.voice.file_id, rawCaption ? { caption:rawCaption, parse_mode:'HTML' } : {});
      else { const textToSend = rawCaption || (msg.text||'').replace(/^\/bc\s*/i,'').trim(); if (textToSend) await bot.sendMessage(uid, textToSend, { parse_mode:'HTML' }); }
      ok++;
    } catch (_) { fail++; }
    await new Promise(r => setTimeout(r, 35));
  }
  await safeDelete(adminChatId, sm.message_id);
  await bot.sendMessage(adminChatId, '✅ <b>Broadcast done!</b>\n👍 Sent: <b>'+ok+'</b>\n❌ Failed: <b>'+fail+'</b>', { parse_mode:'HTML' });
}

// ══════════════════════════════════════════════
//  CALLBACK QUERY HANDLER  (single, unified)
// ══════════════════════════════════════════════
bot.on('callback_query', async cq => {
  const chatId = cq.message.chat.id, msgId = cq.message.message_id, data = cq.data, from = cq.from;
  if (from) registerUser(from);
  try {
    await bot.answerCallbackQuery(cq.id);

    // ── PDF download (result feature) ──────────
    if (data.startsWith('pdf_')) {
      const index = data.replace('pdf_', '');
      const lm = await sendMsg(chatId, '📄 <b>PDF generate කරමින්...</b> ⏳');
      try {
        let result = pdfCache.get(index);
        if (!result) result = await fetchALResult(index);
        if (!result || result.error) { await safeDelete(chatId, lm.message_id); return sendMsg(chatId, '❌ PDF generate කරන්නට result data හමු නොවිණ.'); }
        const pdfBuf = await generateResultPDF(result);
        await safeDelete(chatId, lm.message_id);
        await bot.sendDocument(chatId, pdfBuf, {
          caption: '📄 <b>' + esc(result.name) + '</b>\nIndex: <tg-spoiler>' + esc(result.index) + '</tg-spoiler>\n\n🤖 <i>Powered by @SL_pastpaper_bot</i>',
          parse_mode: 'HTML',
        }, { filename: 'AL_Result_' + result.index + '.pdf', contentType: 'application/pdf' });
      } catch (e) {
        await safeDelete(chatId, lm.message_id);
        console.error('[pdf gen]', e.message);
        await sendMsg(chatId, '❌ PDF error: <code>' + esc(e.message) + '</code>');
      }
      return;
    }

    // ── result_again ────────────────────────────
    if (data === 'result_again') {
      await sendMsg(chatId, '📋 Index number type කරන්න:\n\n📌 Single: <code>/result 5419730</code>\n📌 Bulk:   <code>/results 5419980 5419991</code>');
      return;
    }

    // ── JOIN CHECK ──────────────────────────────
    if (data === 'check_join') {
      const channelStatus = await checkUserJoined(from.id), notJoined = channelStatus.filter(c => !c.joined);
      if (notJoined.length > 0) {
        const stillKb = [...notJoined.map(ch => [{ text: ch.label+' — Join Now', url: ch.link }]), [{ text:'✅ ඔව් Join කළා — Check', callback_data:'check_join' }]];
        try { await bot.editMessageCaption('⚠️ <b>Still not joined!</b>\n\nPlease join ALL channels/groups:\n\n' + notJoined.map(ch => '  ❌ '+ch.label+' — Not joined yet').join('\n') + '\n\nJoin කරලා "✅ ඔව් Join කළා" click කරන්න.', { chat_id:chatId, message_id:msgId, parse_mode:'HTML', reply_markup:{ inline_keyboard:stillKb } }); }
        catch (_) { await bot.answerCallbackQuery(cq.id, { text:'⚠️ Join all channels & groups first!', show_alert:true }); }
        return;
      }
      try { await bot.answerCallbackQuery(cq.id, { text:'✅ Verified! Welcome to SL PastPaper Bot 🎓', show_alert:false }); } catch (_) {}
      registerUser(from);
      await safeDelete(chatId, msgId);
      const confirmMsg = await sendMsg(chatId, '✅ <b>Join confirmed!</b>\n\n👤 <b>User ID:</b> <code>'+from.id+'</code> saved!\n🎓 Welcome to <b>SL PastPaper Bot</b>!\n\n<i>Loading bot...</i>');
      await new Promise(r => setTimeout(r, 1500));
      await safeDelete(chatId, confirmMsg.message_id);
      const sess = getSess(chatId), pendingParam = sess.pendingStartParam || '';
      if (pendingParam) updSess(chatId, { pendingStartParam: null });
      const name = esc(from.first_name || 'Student');
      await showWelcome(chatId, name);
      if (pendingParam && pendingParam.startsWith('dl_')) {
        const dlId = pendingParam.replace('dl_',''), cached = resultCache.get(dlId);
        if (cached) {
          await new Promise(r => setTimeout(r, 500));
          await sendAdThenDownload(chatId, async () => {
            const lm = await sendMsg(chatId, '📥 Downloading <b>'+esc(cached.title)+'</b>...');
            try {
              const links = (cached.allLinks && cached.allLinks.length) ? cached.allLinks : [cached.url];
              let buf = null, lastErr = null;
              for (const link of links) { try { const r = await downloadAnyPdf(link); buf = r.buf; break; } catch (e) { lastErr = e; } }
              if (!buf) throw lastErr || new Error('All download links failed');
              await safeDelete(chatId, lm.message_id);
              const safeTitle = String(cached.title||'paper').replace(/[/\\:*?"<>|]/g,'_').replace(/\s+/g,' ').trim().slice(0,100);
              const srcLabel  = String(cached.source||'').charAt(0).toUpperCase()+String(cached.source||'').slice(1);
              await bot.sendDocument(chatId, buf, { filename:safeTitle+'.pdf', caption:pdfCaption(cached.title,[{label:'📦 Size   :',value:(buf.length/1048576).toFixed(2)+' MB'},{label:'🌐 Source :',value:srcLabel},'─────────────────────','🎓  Good luck with your studies!']), parse_mode:'HTML' });
              if (from) await notifyAdminDownload(from, cached.title, srcLabel);
            } catch (e) { await safeDelete(chatId, lm.message_id); await sendMsg(chatId, '❌ Download failed: '+esc(e.message)); }
          });
        }
      }
      return;
    }

    if (data.startsWith('notepage_')) { const parts = data.split('_'); await showNotePage(chatId, parts.slice(2).join('_'), parseInt(parts[1])); return; }
    if (data.startsWith('listpage_')) { await showListFolders(chatId, parseInt(data.replace('listpage_',''))||1); return; }
    if (data.startsWith('listfolder_')) {
      const raw = data.replace('listfolder_',''), lastU = raw.lastIndexOf('_');
      await showListNotes(chatId, decodeURIComponent(raw.slice(0, lastU)), parseInt(raw.slice(lastU+1))||1, msgId); return;
    }
    if (data.startsWith('ps_')) {
      const parts = data.split('_'), type = parts[1], subject = parts.slice(2).join('_');
      const sm = await sendMsg(chatId, '🔍 Searching <b>'+esc(subject)+'</b>...');
      if (type === 'government') await ppSearch(chatId, subject, from); else await doSearch(chatId, subject, type, 1, from);
      await safeDelete(chatId, sm.message_id); return;
    }
    if (data.startsWith('note_send_')) { const n = resultCache.get('note_' + data.replace('note_send_','')); if (!n) return sendMsg(chatId,'❌ Note expired.'); await deliverNote(chatId,n); return; }
    if (data.startsWith('eth_catpage_')) { const parts = data.replace('eth_catpage_','').split('_'); await ethTypeHandler(chatId, parts.slice(0,-1).join('_'), parseInt(parts[parts.length-1]), msgId); return; }
    if (data.startsWith('eth_type_'))    { await ethTypeHandler(chatId, data.replace('eth_type_',''), 1, msgId); return; }
    if (data.startsWith('eth_subject_')) { const raw = data.replace('eth_subject_',''); const sep = raw.indexOf('|'); await ethSubjectHandler(chatId, raw.slice(0,sep), raw.slice(sep+1)); return; }
    if (data.startsWith('eth_dl_')) {
      const c = resultCache.get('eth_' + data.replace('eth_dl_',''));
      if (!c) return sendMsg(chatId,'❌ Link expired. Please search again.');
      await sendAdThenDownload(chatId, async () => { await ethDownload(chatId, c.pdf_url, c.name, from); }); return;
    }
    if (data.startsWith('page_'))     { await doPagination(chatId, msgId, data, from); return; }
    if (data.startsWith('download_')) { await doPaperDownload(chatId, msgId, data, from); return; }
    if (data.startsWith('year_'))     { await doYearSelection(chatId, msgId, data, from); return; }
    if (data.startsWith('help_'))     { await helpCmd(chatId, msgId, data.replace('help_','')); return; }
    if (data === 'tutorial')          { await tutorialHandler(chatId, msgId, 'main'); return; }
    if (data.startsWith('tut_'))      { await tutorialHandler(chatId, msgId, data.replace('tut_','')); return; }

    if (data.startsWith('group_dl_')) {
      const id = data.replace('group_dl_',''), cached = resultCache.get(id);
      if (!cached) { await bot.answerCallbackQuery(cq.id, { text:'❌ Link expired. Search again.', show_alert:true }); return; }
      const userChatId = from.id, userStarted = !!usersDB[String(userChatId)];
      if (!userStarted) {
        resultCache.set(id, cached, 600);
        await bot.answerCallbackQuery(cq.id, { text:'📲 Bot start කරන්න! Link click කරන්න.', show_alert:true });
        try { await bot.sendMessage(chatId, '📲 <b>'+esc(from.first_name||'User')+'</b>, paper download කරන්න bot start කරන්න:\n\n👆 <a href="https://t.me/SL_pastpaper_bot?start=dl_'+id+'">Click here to start bot &amp; download</a>\n\n📄 <i>'+esc(cached.title)+'</i>', { parse_mode:'HTML', reply_to_message_id:cq.message.message_id }); } catch (_) {}
        return;
      }
      try { await bot.answerCallbackQuery(cq.id, { text:'📥 DM eka check karanna!', show_alert:false }); } catch (_) {}
      await sendAdThenDownload(userChatId, async () => {
        const lm = await sendMsg(userChatId, '📥 Downloading <b>'+esc(cached.title)+'</b>...');
        try {
          const links = (cached.allLinks && cached.allLinks.length) ? cached.allLinks : [cached.url];
          let buf = null, lastErr = null;
          for (const link of links) { try { const r = await downloadAnyPdf(link); buf = r.buf; break; } catch (e) { lastErr = e; } }
          if (!buf) throw lastErr || new Error('All download links failed');
          await safeDelete(userChatId, lm.message_id);
          const safeTitle = String(cached.title||'SL_pastpaper_bot').replace(/[/\\:*?"<>|]/g,'_').replace(/\s+/g,' ').trim().slice(0,100);
          const srcLabel  = String(cached.source||'').charAt(0).toUpperCase()+String(cached.source||'').slice(1);
          await bot.sendDocument(userChatId, buf, { filename:safeTitle+'.pdf', caption:pdfCaption(cached.title,[{label:'📦 Size   :',value:(buf.length/1048576).toFixed(2)+' MB'},{label:'🌐 Source :',value:srcLabel},'─────────────────────','🎓  Good luck with your studies!']), parse_mode:'HTML' });
          if (from) await notifyAdminDownload(from, cached.title, srcLabel);
        } catch (e) { await safeDelete(userChatId, lm.message_id); await sendMsg(userChatId, '❌ <b>Download failed:</b> '+esc(e.message)); }
      });
      return;
    }

    switch (data) {
      case 'main_menu':         await editMsg(chatId,msgId,BOT_IMG,box('Main Menu','📚 <b>SL_pastpaper_bot</b>\n\nChoose an option:'),kbMain()); break;
      case 'search_papers':     await editMsg(chatId,msgId,BOT_IMG,box('Search Papers','🔍 <b>Choose your search source:</b>\n\n📊 <b>Wiki</b> — Community database\n🏛️ <b>Government</b> — Official papers\n💾 <b>Digital</b> — Curated archives\n\nOr use: <code>/wiki</code> <code>/di</code> <code>/pp</code> <code>/ps</code>'),kbSearch()); break;
      case 'help':              await editMsg(chatId,msgId,BOT_IMG,helpListHTML(),kbHelp()); break;
      case 'eth_menu':          await editMsg(chatId,msgId,BOT_IMG,box('E-Thaksalawa Papers','🏫 <b>Official Ministry of Education Papers</b>\n\nSelect paper type:'),kbEthMenu()); break;
      case 'wiki_search':       await searchTypeHandler(chatId,msgId,'wiki'); break;
      case 'government_search': await searchTypeHandler(chatId,msgId,'government'); break;
      case 'digital_search':    await searchTypeHandler(chatId,msgId,'digital'); break;
      case 'note_enable':       updSess(chatId,{noteAutoSend:true});  await sendMsg(chatId,box('Auto-Send Enabled','✅ Note auto-send is <b>ON</b>.'),kbMain()); break;
      case 'note_disable':      updSess(chatId,{noteAutoSend:false}); await sendMsg(chatId,box('Auto-Send Disabled','❌ Note auto-send is <b>OFF</b>.'),kbMain()); break;
      case 'ai_mode_educational': updSess(chatId,{aiMode:'educational',aiEnabled:false}); await sendMsg(chatId,box('AI Mode: Educational','🎓 <b>Educational AI enabled!</b>\n\n✅ Image upload support enabled\n✅ Subject-specific answers\n✅ Sinhala/English support\n\nDisable: /aicontrol'),kbMain()); break;
      case 'ai_mode_user':        updSess(chatId,{aiMode:'user',aiEnabled:true});        await sendMsg(chatId,box('AI Mode: Bot/User AI','🤖 <b>Bot/User AI (chai2) enabled!</b>\n\nDisable: /aicontrol'),kbMain()); break;
      case 'ai_enable':           updSess(chatId,{aiEnabled:true,aiMode:'user'});        await sendMsg(chatId,box('AI Enabled','✅ AI auto-response is <b>ON</b> (Bot/User mode).'),kbMain()); break;
      case 'ai_disable':          updSess(chatId,{aiEnabled:false,aiMode:'off'});        await sendMsg(chatId,box('AI Disabled','❌ AI auto-response is <b>OFF</b>.'),kbMain()); break;
      case 'countdown_init':      await editMsg(chatId,msgId,BOT_IMG,box('Exam Countdown','⏰ <b>Select your A/L exam year:</b>'),kbCountdownYears()); break;
      case 'countdown_year_2026': await safeDelete(chatId,msgId); await sendCountdown(chatId,'2026'); break;
      case 'countdown_year_2027': await safeDelete(chatId,msgId); await sendCountdown(chatId,'2027'); break;
      case 'countdown_enable':  await cdEnable(chatId); break;
      case 'countdown_disable': await cdDisable(chatId); break;
      case 'countdown_reset':   await cdReset(chatId); break;
    }
  } catch (err) {
    console.error('[cb]', err.message);
    try { await sendMsg(chatId, box('Error','❌ Something went wrong.\n<code>'+esc(err.message)+'</code>\n\nPlease try again.')); } catch (_) {}
  }
});

// ══════════════════════════════════════════════
//  HELP & TUTORIAL
// ══════════════════════════════════════════════
function helpListHTML() {
  return box('Help &amp; Commands',
    '📖 <b>All commands:</b>\n\n' +
    '<code>/wiki &lt;subject&gt;</code> — Wiki search\n<code>/di &lt;subject&gt;</code> — Digital archives\n' +
    '<code>/pp &lt;subject&gt;</code> — Gov papers by year\n<code>/ps &lt;subject&gt;</code> — Choose source\n' +
    '<code>/ai &lt;question&gt;</code> — AI answer\n<code>/aiclear</code> — Clear AI history\n' +
    '<code>/note</code> — Upload notes\n<code>/countdown</code> — Exam countdown\n' +
    '<code>/countdownstop</code> — Stop countdown\n<code>/countdowncontrol</code> — Manage countdown\n' +
    '<code>/notecontrol</code> — Note auto-send settings\n<code>/aicontrol</code> — AI settings\n' +
    '<code>/eth</code> — E-Thaksalawa papers\n<code>/result &lt;index&gt;</code> — A/L 2025 result\n' +
    '<code>/results &lt;indexes&gt;</code> — Bulk results\n\n' +
    '🤖 <b>AI Modes:</b>\n  🎓 Educational AI — Subject-specific + image\n  🤖 Bot/User AI — General chatbot\n\n' +
    '<b>Group:</b> <code>/chat on</code> / <code>/chat off</code>\n' +
    '<b>Admin:</b> <code>/bc &lt;msg&gt;</code> · <code>/stats</code>\n\nTap a button for detailed help:'
  );
}

const TUTORIALS = {
  main:      ['Tutorial — Bot Guide',        '📖 <b>Bot Use කරන්නේ කෙසේද?</b>\n\nමෙම bot එක Sri Lanka A/L students ට past papers, notes සහ AI assistance provide කරයි.\n\n📌 <b>Topics:</b>\n  › 🔍 Papers Search\n  › 🏫 E-Thaksalawa Papers\n  › 🤖 AI Assistant\n  › 📝 Note Upload &amp; Auto-Send\n  › ⏰ Exam Countdown\n\nඕනෑ topic එකක් select කරන්න 👇'],
  search:    ['Tutorial — Paper Search',      '🔍 <b>Papers Search කරන්නේ කෙසේද?</b>\n\n<b>Method 1 — Commands:</b>\n• <code>/wiki biology</code>\n• <code>/di chemistry</code>\n• <code>/pp physics</code>\n• <code>/ps accounting</code>\n\n<b>Method 2 — Inline:</b>\n• <code>@SL_pastpaper_bot sinhala 2024</code>\n\n⚠️ Ad 5s shows before download — supports bot!'],
  eth:       ['Tutorial — E-Thaksalawa',      '🏫 <b>E-Thaksalawa Papers:</b>\n\n1. Main Menu → 🏫 E-Thaksalawa\n2. Paper type select\n3. Subject select\n4. Paper tap → download\n\nCommand: <code>/eth</code>'],
  ai:        ['Tutorial — AI Assistant',      '🤖 <b>AI Modes:</b>\n\n🎓 <b>Educational AI:</b> Subject-specific + image upload\n🤖 <b>Bot/User AI:</b> General chatbot\n\nToggle: /aicontrol\n\n💡 Image send + caption = AI analysis!'],
  notes:     ['Tutorial — Note Upload',       '📝 Reply to a file:\n<code>/note subject,description,keyword</code>\n\n• <code>/notecontrol</code> — auto-send on/off'],
  countdown: ['Tutorial — Exam Countdown',    '⏰ <code>/countdown</code> → year select → daily 8AM SLT notify\n\n• <code>/countdownadd 2026.08.11</code>\n• <code>/countdowncontrol</code> — manage\n• <code>/countdownstop</code> — stop'],
  bc:        ['Tutorial — Broadcast (Admin)', '📡 <b>Admin Group Only:</b>\n\n• <code>/bc Your message</code>\n• Media + caption <code>/bc caption</code>\n• <code>/stats</code> — statistics']
};

async function tutorialHandler(chatId, msgId, page) {
  const t = TUTORIALS[page] || TUTORIALS['main'], html = box(t[0], t[1]);
  const kb = page === 'main' ? kbTutorial() : { inline_keyboard: [[{ text:'🔙 Tutorial Menu', callback_data:'tutorial' }, { text:'🏠 Main', callback_data:'main_menu' }]] };
  if (msgId) await editMsg(chatId, msgId, BOT_IMG, html, kb); else await sendPhoto(chatId, BOT_IMG, html, kb);
}

async function helpCmd(chatId, msgId, cmd) {
  const helps = {
    wiki:      ['Wiki Search — /wiki',      '📊 <b>Usage:</b> <code>/wiki &lt;subject&gt;</code>\n\n<b>Examples:</b>\n• <code>/wiki accounting</code>\n• <code>/wiki biology grade 11</code>\n\n⚠️ Ad shows for 5s before download!'],
    di:        ['Digital Archives — /di',   '💾 <b>Usage:</b> <code>/di &lt;subject&gt;</code>\n\n• <code>/di chemistry</code>\n• <code>/di physics term test</code>'],
    pp:        ['Government Papers — /pp',  '🏛️ <b>Usage:</b> <code>/pp &lt;subject&gt;</code>\n\nSearches 2010–2020, shows year buttons.'],
    ps:        ['Source Select — /ps',      '📋 <b>Usage:</b> <code>/ps &lt;subject&gt;</code>\n\nChoose Wiki, Government, or Digital.'],
    ai:        ['AI Assistant — /ai',       '🤖 <b>Usage:</b> <code>/ai &lt;question&gt;</code>\n\n🎓 Educational AI — exam + image\n🤖 Bot/User AI — general\n\nToggle: /aicontrol'],
    note:      ['Note Upload — /note',      '📝 Reply to a file:\n<code>/note &lt;subject&gt;,&lt;desc&gt;,&lt;autosend&gt;</code>'],
    countdown: ['Countdown — /countdown',   '⏰ Select year. Daily 8AM SLT.\n/countdowncontrol — manage\n/countdownstop — stop'],
    eth:       ['E-Thaksalawa — /eth',      '🏫 <b>Usage:</b> <code>/eth</code>\n\nOfficial Ministry of Education papers.']
  };
  const h = helps[cmd] || ['Help', 'No details available.'];
  await editMsg(chatId, msgId, BOT_IMG, box(h[0], h[1]), kbBack('help'));
}

// ══════════════════════════════════════════════
//  SEARCH
// ══════════════════════════════════════════════
async function searchTypeHandler(chatId, msgId, type) {
  updSess(chatId, { searchType: type, waitingForQuery: true });
  const names = { wiki:'Wiki Search', government:'Government Papers', digital:'Digital Archives' };
  await sendPhoto(chatId, BOT_IMG, box(names[type], '🔍 <b>'+esc(names[type])+'</b> selected\n\n📝 Now type your subject name:\n\n<b>Examples:</b> <code>accounting</code>  <code>mathematics</code>  <code>biology</code>'), { inline_keyboard: [[{ text:'🔙 Main Menu', callback_data:'main_menu' }]] });
  await safeDelete(chatId, msgId);
}

bot.onText(/\/wiki (.+)/, async (msg, match) => {
  if (!isChatAllowed(msg)) return; registerUser(msg.from);
  const chatId = msg.chat.id, q = match[1].trim();
  const sm = await sendMsg(chatId, '🔍 Searching Wiki for <b>'+esc(q)+'</b>...');
  await doSearch(chatId, q, 'wiki', 1, msg.from, msg.chat.type==='group'||msg.chat.type==='supergroup');
  await safeDelete(chatId, sm.message_id);
});
bot.onText(/\/di (.+)/, async (msg, match) => {
  if (!isChatAllowed(msg)) return; registerUser(msg.from);
  const chatId = msg.chat.id, q = match[1].trim();
  const sm = await sendMsg(chatId, '🔍 Searching Digital Archives for <b>'+esc(q)+'</b>...');
  await doSearch(chatId, q, 'digital', 1, msg.from, msg.chat.type==='group'||msg.chat.type==='supergroup');
  await safeDelete(chatId, sm.message_id);
});
bot.onText(/\/pp (.+)/, async (msg, match) => {
  if (!isChatAllowed(msg)) return; registerUser(msg.from);
  const chatId = msg.chat.id, q = match[1].trim();
  const sm = await sendMsg(chatId, '🔍 Searching Government Papers for <b>'+esc(q)+'</b>...');
  await ppSearch(chatId, q, msg.from); await safeDelete(chatId, sm.message_id);
});
bot.onText(/\/ps (.+)/, async (msg, match) => { if (!isChatAllowed(msg)) return; registerUser(msg.from); await psPrompt(msg.chat.id, match[1].trim()); });
bot.onText(/\/eth/, async msg => { if (!isChatAllowed(msg)) return; registerUser(msg.from); await sendPhoto(msg.chat.id, BOT_IMG, box('E-Thaksalawa Papers','🏫 <b>Official Ministry of Education Papers</b>\n\nSelect paper type below:'), kbEthMenu()); });

bot.onText(/\/ai (.+)/, async (msg, match) => {
  if (!isChatAllowed(msg)) return; registerUser(msg.from);
  const chatId = msg.chat.id, q = match[1].trim();
  if (msg.reply_to_message) {
    const replied = msg.reply_to_message;
    if (replied.photo || (replied.document && replied.document.mime_type && replied.document.mime_type.startsWith('image/'))) {
      const lm = await sendMsg(chatId, '📤 <b>Image upload කරමින්...</b> Please wait ⏳');
      try {
        const imageFileId = replied.photo ? replied.photo[replied.photo.length-1].file_id : replied.document.file_id;
        const fileObj = await bot.getFile(imageFileId);
        const imgRes  = await axios.get('https://api.telegram.org/file/bot'+token+'/'+fileObj.file_path, { responseType:'arraybuffer', timeout:30000 });
        const catboxUrl = await uploadToCatbox(Buffer.from(imgRes.data), 'img_'+Date.now()+'.'+(fileObj.file_path.split('.').pop()||'jpg'));
        await safeDelete(chatId, lm.message_id);
        await sendEducationalAI(chatId, q, catboxUrl);
      } catch (e) { await safeDelete(chatId, lm.message_id); await sendMsg(chatId, '❌ Image error: '+esc(e.message)); }
      return;
    }
  }
  await sendAI(chatId, q);
});

bot.onText(/\/aicontrol/, async msg => {
  if (!isChatAllowed(msg)) return; registerUser(msg.from);
  const chatId = msg.chat.id, s = getSess(chatId);
  const currentMode = s.aiMode || (s.aiEnabled ? 'user' : 'off');
  const modeLabels  = { educational:'🎓 Educational AI', user:'🤖 Bot/User AI', off:'❌ Disabled' };
  const isGroup = msg.chat.type==='group'||msg.chat.type==='supergroup';
  await sendPhoto(chatId, BOT_IMG, box('AI Control','🤖 <b>Current mode:</b> '+(modeLabels[currentMode]||'❌ Disabled')+(isGroup?'\n\n<i>📌 Group mode: AI enable කළාම ඕනෑ message ම AI ට reply කරනවා.</i>':'')+'\n\nSelect AI mode:'), kbAICtrl());
});
bot.onText(/\/aiclear/, async msg => {
  if (!isChatAllowed(msg)) return; registerUser(msg.from);
  clearHistory(msg.chat.id);
  await sendMsg(msg.chat.id, box('AI History Cleared','🧹 <b>Conversation history cleared!</b>\n\nFresh start. Use /ai to ask.'), kbMain());
});

// ══════════════════════════════════════════════
//  COUNTDOWN COMMANDS
// ══════════════════════════════════════════════
bot.onText(/\/countdown/, async msg => {
  if (!isChatAllowed(msg)) return; registerUser(msg.from);
  const chatId = msg.chat.id, uFile = path.join(COUNTDOWN_DIR, chatId+'.json');
  if (fs.existsSync(uFile)) { try { const s = JSON.parse(fs.readFileSync(uFile)); if (s.year) { await sendCountdown(chatId, s.year, s.customDate ? new Date(s.customDate) : null); return; } } catch (_) {} }
  await sendPhoto(chatId, BOT_IMG, box('Exam Countdown','⏰ <b>Select your A/L exam year:</b>\n\nDaily countdown will start after selection.'), kbCountdownYears());
});
bot.onText(/\/countdownstop/, async msg => {
  if (!isChatAllowed(msg)) return;
  const chatId = msg.chat.id, uFile = path.join(COUNTDOWN_DIR, chatId+'.json');
  if (fs.existsSync(uFile)) { try { fs.unlinkSync(uFile); if (jobs[chatId]) { jobs[chatId].cancel(); delete jobs[chatId]; } await sendMsg(chatId, box('Countdown Stopped','🛑 Countdown stopped.\nRestart anytime with /countdown'), kbMain()); } catch (e) { await sendMsg(chatId, box('Error','❌ '+esc(e.message))); } }
  else { await sendMsg(chatId, box('No Countdown','🛑 No active countdown.\nStart with /countdown'), kbMain()); }
});
bot.onText(/\/countdowncontrol/, async msg => {
  if (!isChatAllowed(msg)) return;
  const chatId = msg.chat.id, uFile = path.join(COUNTDOWN_DIR, chatId+'.json');
  let info = 'No active countdown found.';
  if (fs.existsSync(uFile)) { try { const s = JSON.parse(fs.readFileSync(uFile)); info = '📅 <b>Year:</b> '+esc(s.year)+'\n🔔 <b>Notifications:</b> '+(s.notifications!==false?'✅ Enabled':'❌ Disabled'); } catch (_) {} }
  await sendPhoto(chatId, BOT_IMG, box('Countdown Control', info+'\n\nManage below:'), kbCountdownCtrl());
});
bot.onText(/\/countdownadd (.+)/, async (msg, match) => {
  if (!isChatAllowed(msg)) return;
  const chatId = msg.chat.id, date = match[1].trim();
  if (!/^\d{4}\.\d{2}\.\d{2}$/.test(date)) return sendMsg(chatId, box('Error','❌ Format: <code>/countdownadd YYYY.MM.DD</code>'));
  try {
    const [y,m,d] = date.split('.');
    const examDate = new Date(y+'-'+m+'-'+d+'T00:00:00+05:30');
    if (isNaN(examDate.getTime()) || examDate < new Date()) throw new Error('Invalid or past date.');
    const uFile = path.join(COUNTDOWN_DIR, chatId+'.json');
    if (fs.existsSync(uFile)) fs.unlinkSync(uFile);
    fs.writeFileSync(uFile, JSON.stringify({ year:y, customDate:examDate.toISOString(), notifications:true }, null, 2));
    await sendCountdown(chatId, y, examDate);
  } catch (e) { await sendMsg(chatId, box('Error','❌ '+esc(e.message))); }
});

// ── Private-only commands ──────────────────────
bot.onText(/\/note (.+)/, async (msg, match) => {
  if (msg.chat.type !== 'private') return; registerUser(msg.from);
  const chatId = msg.chat.id;
  try {
    const parts = match[1].trim().split(',').map(s => s.trim());
    if (parts.length !== 3 || parts.some(p => !p)) throw new Error('Format: /note subject,description,autosend_name');
    const [subject, description, autoSendName] = parts;
    const quoted = msg.reply_to_message;
    if (!quoted) throw new Error('Reply to a file with the /note command');
    const mimeType = (quoted.document && quoted.document.mime_type) || (quoted.photo ? 'image/jpeg' : null) || (quoted.audio && quoted.audio.mime_type) || '';
    if (!mimeType) throw new Error('Reply to an image, PDF, or audio file');
    let buf;
    if (quoted.photo) { const file = await bot.getFile(quoted.photo[quoted.photo.length-1].file_id); buf = (await axios.get('https://api.telegram.org/file/bot'+token+'/'+file.file_path,{responseType:'arraybuffer'})).data; }
    else { const fid = (quoted.document&&quoted.document.file_id)||(quoted.audio&&quoted.audio.file_id); const file = await bot.getFile(fid); buf = (await axios.get('https://api.telegram.org/file/bot'+token+'/'+file.file_path,{responseType:'arraybuffer'})).data; }
    const extMap = {'image/jpeg':'.jpg','image/png':'.png','audio/mpeg':'.mp3','application/pdf':'.pdf'};
    const ext = extMap[mimeType] || (mimeType.includes('audio')?'.mp3':mimeType.includes('pdf')?'.pdf':null);
    if (!ext) throw new Error('Unsupported file type');
    const tmp = path.join(os.tmpdir(), 'note_'+Date.now()+ext);
    fs.writeFileSync(tmp, buf);
    const form = new FormData(); form.append('fileToUpload', fs.createReadStream(tmp), 'note'+ext); form.append('reqtype','fileupload');
    const res = await axios.post('https://catbox.moe/user/api.php', form, { headers:form.getHeaders() });
    fs.unlinkSync(tmp);
    const dir = path.join(DATA_DIR, subject);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive:true });
    fs.writeFileSync(path.join(dir, Date.now()+'_'+description+'.json'), JSON.stringify({ description, autoSendName, url:res.data, timestamp:new Date().toISOString() }, null, 2));
    await sendMsg(chatId, box('Note Uploaded ✅', '📁 <b>Subject:</b> '+esc(subject)+'\n📝 <b>Description:</b> '+esc(description)+'\n🔑 <b>Auto-send name:</b> <code>'+esc(autoSendName)+'</code>\n🔗 <b>URL:</b> '+esc(res.data)), kbMain());
  } catch (e) { await sendMsg(chatId, box('Error','❌ '+esc(e.message))); }
});
bot.onText(/\/notecontrol/, async msg => {
  if (msg.chat.type !== 'private') return; registerUser(msg.from);
  const s = getSess(msg.chat.id);
  await sendPhoto(msg.chat.id, BOT_IMG, box('Note Auto-Send','📝 <b>Current:</b> '+(s.noteAutoSend!==false?'✅ Enabled':'❌ Disabled')+'\n\nToggle below:'), kbNoteCtrl());
});

// ══════════════════════════════════════════════
//  /list — Note Folders Browser
// ══════════════════════════════════════════════
const LIST_FOLDERS_PER_PAGE = 20, LIST_NOTES_PER_PAGE = 15;
function getNoteSubjects() {
  if (!fs.existsSync(DATA_DIR)) return [];
  try { return fs.readdirSync(DATA_DIR).filter(f => { try { return fs.statSync(path.join(DATA_DIR,f)).isDirectory()&&f!=='countdown'; } catch(_){return false;} }).sort(); } catch(_){return[];}
}
function getNotesBySubject(subject) {
  const dir = path.join(DATA_DIR, subject), notes = [];
  if (!fs.existsSync(dir)) return notes;
  try { fs.readdirSync(dir).filter(f=>f.endsWith('.json')).forEach(file => { try { const d=JSON.parse(fs.readFileSync(path.join(dir,file))); notes.push(Object.assign({},d,{subject,_file:file})); }catch(_){} }); } catch(_){}
  return notes;
}
bot.onText(/\/list/, async msg => { if (msg.chat.type!=='private') return; registerUser(msg.from); await showListFolders(msg.chat.id,1); });
async function showListFolders(chatId, page) {
  const subs = getNoteSubjects();
  if (!subs.length) return sendMsg(chatId, box('Note Folders','📂 No note folders found.\n\nAdd notes with <code>/note</code> command.'), kbMain());
  const total = Math.ceil(subs.length/LIST_FOLDERS_PER_PAGE), start=(page-1)*LIST_FOLDERS_PER_PAGE;
  const kb = subs.slice(start,start+LIST_FOLDERS_PER_PAGE).map(sub => [{ text:'📂 '+sub+'  ('+getNotesBySubject(sub).length+' notes)', callback_data:'listfolder_'+encodeURIComponent(sub)+'_1' }]);
  const navRow = [];
  if (page>1)     navRow.push({ text:'◀️ Prev', callback_data:'listpage_'+(page-1) });
  if (page<total) navRow.push({ text:'Next ▶️', callback_data:'listpage_'+(page+1) });
  if (navRow.length) kb.push(navRow);
  kb.push([{ text:'🏠 Main Menu', callback_data:'main_menu' }]);
  await sendPhoto(chatId, BOT_IMG, box('Note Folders','📂 <b>'+subs.length+'</b> folders\n📄 Page <b>'+page+'</b> / <b>'+total+'</b>\n\nSelect a folder:'), { inline_keyboard:kb });
}
async function showListNotes(chatId, subject, page, msgId) {
  const notes = getNotesBySubject(subject);
  if (!notes.length) return sendMsg(chatId, box('No Notes','📂 No notes in <b>'+esc(subject)+'</b>.'), { inline_keyboard:[[{ text:'🔙 Folders', callback_data:'listpage_1' }]] });
  const total=Math.ceil(notes.length/LIST_NOTES_PER_PAGE), start=(page-1)*LIST_NOTES_PER_PAGE;
  const kb = notes.slice(start,start+LIST_NOTES_PER_PAGE).map(n => { const h=sid(n._file+subject+(n.url||'')); resultCache.set('note_'+h,n,300); return [{ text:'📄 '+(n.description||n.autoSendName||'Note').slice(0,45), callback_data:'note_send_'+h }]; });
  const navRow=[];
  if (page>1)     navRow.push({ text:'◀️ Prev', callback_data:'listfolder_'+encodeURIComponent(subject)+'_'+(page-1) });
  if (page<total) navRow.push({ text:'Next ▶️', callback_data:'listfolder_'+encodeURIComponent(subject)+'_'+(page+1) });
  if (navRow.length) kb.push(navRow);
  kb.push([{ text:'🔙 Folders', callback_data:'listpage_1' },{ text:'🏠 Main', callback_data:'main_menu' }]);
  const html = box('📂 '+esc(subject),'📝 <b>'+notes.length+'</b> notes\n📄 Page <b>'+page+'</b> / <b>'+total+'</b>\n\nTap a note to send it:');
  if (msgId) { try { await bot.editMessageText(html,{ chat_id:chatId, message_id:msgId, parse_mode:'HTML', reply_markup:{ inline_keyboard:kb } }); } catch(_){ await sendMsg(chatId,html,{ inline_keyboard:kb }); } }
  else await sendMsg(chatId, html, { inline_keyboard:kb });
}

// ══════════════════════════════════════════════
//  COUNTDOWN LOGIC
// ══════════════════════════════════════════════
async function cdEnable(chatId) {
  const uFile = path.join(COUNTDOWN_DIR, chatId+'.json');
  if (!fs.existsSync(uFile)) return sendMsg(chatId, box('No Countdown','🛑 No active countdown.\nStart with /countdown'), kbMain());
  try { const s=JSON.parse(fs.readFileSync(uFile)); s.notifications=true; fs.writeFileSync(uFile,JSON.stringify(s,null,2)); schedCD(chatId,uFile); await sendMsg(chatId,box('Notifications Enabled','✅ Daily countdown at 8AM SLT is ON.'),kbMain()); } catch(e){ await sendMsg(chatId,box('Error','❌ '+esc(e.message))); }
}
async function cdDisable(chatId) {
  const uFile = path.join(COUNTDOWN_DIR, chatId+'.json');
  if (!fs.existsSync(uFile)) return sendMsg(chatId, box('No Countdown','🛑 No active countdown.'), kbMain());
  try { const s=JSON.parse(fs.readFileSync(uFile)); s.notifications=false; fs.writeFileSync(uFile,JSON.stringify(s,null,2)); if(jobs[chatId]){jobs[chatId].cancel();delete jobs[chatId];} await sendMsg(chatId,box('Notifications Disabled','❌ Daily countdown is OFF.'),kbMain()); } catch(e){ await sendMsg(chatId,box('Error','❌ '+esc(e.message))); }
}
async function cdReset(chatId) {
  const uFile = path.join(COUNTDOWN_DIR, chatId+'.json');
  if (!fs.existsSync(uFile)) return sendMsg(chatId, box('No Countdown','🛑 No active countdown.'), kbMain());
  try { if(jobs[chatId]){jobs[chatId].cancel();delete jobs[chatId];} fs.unlinkSync(uFile); await sendMsg(chatId,box('Countdown Reset','🔄 Reset done. Start fresh with /countdown'),kbMain()); } catch(e){ await sendMsg(chatId,box('Error','❌ '+esc(e.message))); }
}
function schedCD(chatId, uFile) {
  if (jobs[chatId]) return;
  jobs[chatId] = schedule.scheduleJob('30 2 * * *', async () => {
    try { if (!fs.existsSync(uFile)) return; const s=JSON.parse(fs.readFileSync(uFile)); if (s.notifications) await sendCountdown(chatId, s.year, s.customDate?new Date(s.customDate):null); }
    catch (e) { console.error('[schedCD '+chatId+']', e.message); }
  });
}
async function sendCountdown(chatId, year, customDate) {
  customDate = customDate || null;
  const examDate = customDate || EXAM_DATES[year];
  if (!examDate) return sendMsg(chatId, box('Error','❌ Invalid year: '+esc(year)));
  const nowUTC = new Date(), diff = examDate.getTime() - nowUTC.getTime();
  if (diff <= 0) return sendMsg(chatId, box('Exam Passed','📅 The '+esc(year)+' A/L exam date has passed!\nStart fresh with /countdown'), kbMain());
  const days=Math.floor(diff/86400000), hours=Math.floor((diff%86400000)/3600000), mins=Math.floor((diff%3600000)/60000);
  const weeks=Math.floor(days/7), months=Math.floor(days/30);
  let quote = 'දිනෙකින් දිනය ඉදිරියට යන්න, ඔබට පුළුවන්! 🚀';
  try { const q=await askAI('Generate a very short sinhala motivational quote for A/L students. Only the quote, no extra text.',null); if(q&&q.length<220&&!q.startsWith('❌')&&!q.startsWith('⚠️')) quote=q; } catch(_){}
  const canvas=createCanvas(1280,720), ctx=canvas.getContext('2d');
  try { const bg=await loadImage(CD_BG); const sc=Math.max(1280/bg.width,720/bg.height); const sw=bg.width*sc,sh=bg.height*sc; ctx.drawImage(bg,(1280-sw)/2,(720-sh)/2,sw,sh); } catch(_){ ctx.fillStyle='#0d1b2a'; ctx.fillRect(0,0,1280,720); }
  ctx.fillStyle='#000'; ctx.textAlign='center';
  ctx.font='bold 160px sans-serif'; ctx.fillText(String(days),640,370);
  ctx.font='58px sans-serif';       ctx.fillText('Days Left',640,460);
  ctx.font='32px sans-serif';       ctx.fillText('A/L Exam '+year,640,530);
  const buf=canvas.toBuffer('image/png');
  const tmp=path.join(os.tmpdir(),'cd_'+chatId+'_'+Date.now()+'.png');
  fs.writeFileSync(tmp,buf);
  const todaySL=slDateStr(nowUTC);
  const caption=['🎓  <b>A/L EXAM COUNTDOWN</b>  🎓','','🗓️  <b>'+esc(year)+' Advanced Level</b>','','📆  <b>දින</b>   →  <code>'+days+'</code>  days','🗓️  <b>සති</b>   →  <code>'+weeks+'</code>  weeks','📅  <b>මාස</b>   →  <code>'+months+'</code>  months','⏰  <b>පැය</b>   →  <code>'+hours+'</code>  hours','','📌  <b>Today :</b>  <code>'+todaySL+'</code>','','✨  <i>'+esc(quote)+'</i>','','⚙️ /countdowncontrol    🛑 /countdownstop'].join('\n');
  try {
    await bot.sendPhoto(chatId, tmp, { caption, parse_mode:'HTML' });
    const uFile=path.join(COUNTDOWN_DIR,chatId+'.json'); let ex={};
    try { if(fs.existsSync(uFile)) ex=JSON.parse(fs.readFileSync(uFile)); } catch(_){}
    const settings=Object.assign({},ex,{year,notifications:ex.notifications!==false});
    if (customDate) settings.customDate=customDate.toISOString();
    if (fs.existsSync(uFile)) fs.unlinkSync(uFile);
    fs.writeFileSync(uFile,JSON.stringify(settings,null,2));
    schedCD(chatId,uFile);
  } catch(e){ console.error('[sendCountdown]',e.message); await sendMsg(chatId,box('Error','❌ '+esc(e.message))); }
  finally { try { fs.unlinkSync(tmp); } catch(_){} }
}
function restoreCountdownJobs() {
  if (!fs.existsSync(COUNTDOWN_DIR)) return;
  try { fs.readdirSync(COUNTDOWN_DIR).filter(f=>f.endsWith('.json')).forEach(file => { try { const uFile=path.join(COUNTDOWN_DIR,file); const s=JSON.parse(fs.readFileSync(uFile)); const chatId=parseInt(file.replace('.json','')); if(s.notifications!==false&&chatId){schedCD(chatId,uFile);console.log('[restore] Countdown job for',chatId);} }catch(_){} }); } catch(_){}
}

// ══════════════════════════════════════════════
//  E-THAKSALAWA UI
// ══════════════════════════════════════════════
const ETH_CATS_PER_PAGE = 8;
async function ethTypeHandler(chatId, type, page, msgId) {
  page=page||1; const course=ETH_COURSES[type]; if(!course) return;
  const loadMsg=await sendMsg(chatId,course.emoji+' Loading categories...');
  const cats=await ethCats(type);
  await safeDelete(chatId,loadMsg.message_id);
  if (!cats||!cats.length) { const errKb=kbBack('eth_menu'); if(msgId) return editMsg(chatId,msgId,BOT_IMG,box('Error','❌ Could not load categories. Try again later.'),errKb); return sendMsg(chatId,box('Error','❌ Could not load categories. Try again later.'),errKb); }
  const total=Math.ceil(cats.length/ETH_CATS_PER_PAGE), start=(page-1)*ETH_CATS_PER_PAGE;
  const kb=cats.slice(start,start+ETH_CATS_PER_PAGE).map(cat => { const label=cat.length>45?cat.slice(0,44)+'…':cat; const cbData='eth_subject_'+type+'|'+cat; if(Buffer.byteLength(cbData,'utf8')>64){const h=sid(type+cat);resultCache.set('ethcat_'+h,{type,cat});return[{text:label,callback_data:'eth_subject_'+type+'|__'+h}];} return[{text:label,callback_data:cbData}]; });
  const navRow=[];
  if(page>1)     navRow.push({text:'◀️ Prev',callback_data:'eth_catpage_'+type+'_'+(page-1)});
  if(page<total) navRow.push({text:'Next ▶️',callback_data:'eth_catpage_'+type+'_'+(page+1)});
  if(navRow.length) kb.push(navRow);
  kb.push([{text:'🔙 Back',callback_data:'eth_menu'}]);
  const html=box(course.label,course.emoji+' <b>'+esc(course.label)+'</b>\n\n📚 Found <b>'+cats.length+'</b> subjects\n📄 Page <b>'+page+'</b> of <b>'+total+'</b>\n\nSelect a subject:');
  if(msgId) await editMsg(chatId,msgId,BOT_IMG,html,{inline_keyboard:kb}); else await sendPhoto(chatId,BOT_IMG,html,{inline_keyboard:kb});
}
async function ethSubjectHandler(chatId, type, catRaw) {
  let cat=catRaw;
  if(cat.startsWith('__')){const c=resultCache.get('ethcat_'+cat.slice(2));if(c){type=c.type;cat=c.cat;}else return sendMsg(chatId,'❌ Session expired. Search again.');}
  const course=ETH_COURSES[type]; if(!course) return;
  const lm=await sendMsg(chatId,'📄 Loading papers for <b>'+esc(cat)+'</b>...');
  const papers=await ethPapers(type,cat);
  await safeDelete(chatId,lm.message_id);
  if(!papers||!papers.length) return sendMsg(chatId,box('Not Found','❌ No papers found in <b>'+esc(cat)+'</b>.'),kbBack('eth_menu'));
  const valid=papers.filter(p=>p.pdf_url);
  if(!valid.length) return sendMsg(chatId,box('Not Found','❌ No downloadable papers in <b>'+esc(cat)+'</b>.'),kbBack('eth_menu'));
  const kb=valid.slice(0,15).map(p=>{const label=p.name.length>45?p.name.slice(0,44)+'…':p.name;const h=sid(p.pdf_url+p.name);resultCache.set('eth_'+h,{pdf_url:p.pdf_url,name:p.name});return[{text:'📄 '+label,callback_data:'eth_dl_'+h}];});
  kb.push([{text:'🔙 Back',callback_data:'eth_type_'+type}]);
  await sendPhoto(chatId,BOT_IMG,box(cat,course.emoji+' <b>'+esc(cat)+'</b>\n\nFound <b>'+valid.length+'</b> papers.\nTap to download:'),{inline_keyboard:kb});
}
async function ethDownload(chatId, pdfUrl, paperName, from) {
  const lm=await sendMsg(chatId,'⏳ Downloading <b>'+esc(paperName)+'</b>...');
  try {
    const res=await axios.get(pdfUrl,{responseType:'arraybuffer',timeout:30000,maxRedirects:5,headers:{'User-Agent':ETH_UA,Accept:'application/pdf,*/*',Referer:'https://e-thaksalawa.moe.gov.lk/'}});
    const buf=Buffer.from(res.data),ct=res.headers['content-type']||'';
    if(!ct.includes('pdf')&&!buf.slice(0,5).toString().startsWith('%PDF')) throw new Error('Not a valid PDF');
    if(buf.length>50*1024*1024) throw new Error('File too large');
    await safeDelete(chatId,lm.message_id);
    await bot.sendDocument(chatId,buf,{filename:paperName.replace(/[^a-zA-Z0-9 _\-(). \u0D80-\u0DFF]/g,'_')+'.pdf',caption:pdfCaption(paperName,[{label:'📦 Size   :',value:(buf.length/1048576).toFixed(2)+' MB'},{label:'🌐 Source :',value:'E-Thaksalawa (Official)'},'─────────────────────','🎓  Good luck with your studies!']),parse_mode:'HTML'});
    if(from) await notifyAdminDownload(from,paperName,'E-Thaksalawa');
  } catch(e){ await safeDelete(chatId,lm.message_id); await sendPhoto(chatId,BOT_IMG,box('Download Error','❌ <b>Failed:</b> '+esc(e.message)+'\n\nManual: '+esc(pdfUrl)),kbBack('eth_menu')); }
}

// ══════════════════════════════════════════════
//  SEARCH LOGIC
// ══════════════════════════════════════════════
async function psPrompt(chatId, subject) {
  await sendPhoto(chatId, BOT_IMG, box('Search: "'+esc(subject)+'"','Choose your preferred source to search for <b>'+esc(subject)+'</b>:'), kbSource(subject));
}
async function doSearch(chatId, query, type, page, from, isGroupMode) {
  page=page||1; isGroupMode=isGroupMode||false;
  const lm=await sendMsg(chatId,'🔍 Finding papers... please wait.');
  try {
    const ck=type+'_'+query; let data=searchCache.get(ck);
    if (!data) {
      const urls={wiki:'https://chwiki.netlify.app/?q='+encodeURIComponent(query),digital:'https://chathuradigital.netlify.app/scrape?search='+encodeURIComponent(query),government:'https://chathurapsdl.netlify.app/api/psdl?search='+encodeURIComponent(query)};
      const res=await axios.get(urls[type],{timeout:10000}); data=res.data;
      if(type==='wiki'){if(!data.status||!data.results||!data.results.length) throw new Error('No papers found in Wiki'); data.results=data.results.filter(r=>r.pdfLinks&&r.pdfLinks.length>0).map(r=>Object.assign({},r,{downloadDetails:{download:r.pdfLinks[0]},_allLinks:r.pdfLinks}));}
      else if(type==='digital'){if(!data.message||!data.results||!data.results.length) throw new Error('No papers found in Digital Archives'); data.results=data.results.filter(r=>r.download_links&&r.download_links.length).map(r=>{const title=(r.title||r.name||r.filename||r.subject||'Paper').trim();const links=r.download_links.map(lk=>(typeof lk==='string'?lk:(lk&&lk.url?lk.url:null))).filter(Boolean);if(!links.length)return null;return{title,downloadDetails:{download:links[0]},_allLinks:links};}).filter(Boolean);}
      else if(type==='government'){if(!data.success||!data.papers||!data.papers.length) throw new Error('No papers found in Government Archives'); data.results=data.papers.map(p=>({title:(p.subject+' '+(data.year||'')).trim(),downloadDetails:{download:p.downloadLink}}));}
      if(!data.results||!data.results.length) throw new Error('No downloadable papers found');
      data.results=data.results.map(r=>{const id=sid(r.downloadDetails.download+'||'+r.title);resultCache.set(id,{url:r.downloadDetails.download,allLinks:r._allLinks||[r.downloadDetails.download],title:r.title||'Paper',source:type});return Object.assign({},r,{shortId:id});});
      searchCache.set(ck,data);
    }
    const perPage=5,start=(page-1)*perPage,sliced=data.results.slice(start,start+perPage),total=Math.ceil(data.results.length/perPage);
    const buttons=sliced.map(r=>{const title=r.title.slice(0,48)+(r.title.length>48?'…':'');return isGroupMode?[{text:'📥 '+title,callback_data:'group_dl_'+r.shortId}]:[{text:'📄 '+title,callback_data:'download_'+r.shortId}];});
    const groupNote=isGroupMode?'\n\n💬 <i>Download eka tap karala DM eka check karanna!</i>':'';
    kbPagination(page,total,type,query).inline_keyboard.forEach(row=>buttons.push(row));
    await safeDelete(chatId,lm.message_id);
    await sendPhoto(chatId,BOT_IMG,box('Search Results','📊 Found <b>'+data.results.length+'</b> papers for <b>"'+esc(query)+'"</b>\n\n📖 Page '+page+' of '+total+' — tap a paper to download:'+groupNote),{inline_keyboard:buttons});
  } catch(e){ await safeDelete(chatId,lm.message_id); await sendPhoto(chatId,BOT_IMG,box('Search Error','❌ <b>'+esc(e.message)+'</b>\n\nTry different terms or check spelling.'),kbBack()); }
}
async function ppSearch(chatId, subject, from) {
  const lm=await sendMsg(chatId,'🔍 Searching across years... please wait.');
  try {
    const found=[];
    for(let y=2010;y<=2020;y++){try{const res=await axios.get('https://chathurapsdl.netlify.app/api/psdl?year='+y+'&search='+encodeURIComponent(subject),{timeout:5000});if(res.data.success&&res.data.papers&&res.data.papers.length)found.push({year:y,downloadLink:res.data.papers[0].downloadLink,subject});}catch(_){}}
    if(!found.length) throw new Error('No papers found for "'+subject+'" (2010–2020)');
    const buttons=found.map(p=>{const id=sid(JSON.stringify(p));yearCache.set(id,Object.assign({},p,{_from:from||null}));return[{text:'📅 '+p.year,callback_data:'year_'+id}];});
    buttons.push([{text:'🏠 Main Menu',callback_data:'main_menu'}]);
    await safeDelete(chatId,lm.message_id);
    await sendPhoto(chatId,BOT_IMG,box('Papers by Year','📚 <b>'+esc(subject)+'</b>\n\nFound in <b>'+found.length+'</b> years — select a year:'),{inline_keyboard:buttons});
  } catch(e){ await safeDelete(chatId,lm.message_id); await sendPhoto(chatId,BOT_IMG,box('Not Found','❌ No papers found for <b>"'+esc(subject)+'"</b>.\n\nTry a different subject name.'),kbBack()); }
}
async function doPagination(chatId, msgId, data, from) {
  const parts=data.split('_'),type=parts[1],page=parseInt(parts[parts.length-1]),query=parts.slice(2,parts.length-1).join('_');
  const lm=await sendMsg(chatId,'🔍 Loading page...'); await safeDelete(chatId,msgId);
  await doSearch(chatId,query,type,page,from); await safeDelete(chatId,lm.message_id);
}

async function downloadGoogleDrive(fileId) {
  const baseUrl='https://drive.google.com/uc?export=download&id='+fileId; const jar={};
  function cookieStr(){return Object.entries(jar).map(([k,v])=>k+'='+v).join('; ');}
  function parseCookies(headers){const sc=headers['set-cookie']||[];for(const c of sc){const m=c.match(/^([^=]+)=([^;]*)/);if(m)jar[m[1].trim()]=m[2].trim();}}
  const hdrs=()=>({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','Accept':'text/html,application/xhtml+xml,application/pdf,*/*;q=0.9','Cookie':cookieStr()});
  let res=await axios.get(baseUrl,{responseType:'arraybuffer',maxRedirects:5,timeout:30000,headers:hdrs()}); parseCookies(res.headers);
  let buf=Buffer.from(res.data),ct=res.headers['content-type']||'';
  if(ct.includes('text/html')){
    const html=buf.toString('utf8'); let confirmUrl=null;
    const formMatch=html.match(/action="(\/uc\?[^"]+)"/);
    if(formMatch){const action=formMatch[1].replace(/&amp;/g,'&');const confMatch=html.match(/name="confirm"\s+value="([^"]+)"/);confirmUrl='https://drive.google.com'+action+'&confirm='+(confMatch?confMatch[1]:'t');}
    if(!confirmUrl){const linkMatch=html.match(/href="(\/uc\?export=download[^"]+confirm[^"]+)"/);if(linkMatch)confirmUrl='https://drive.google.com'+linkMatch[1].replace(/&amp;/g,'&');}
    if(!confirmUrl){const uuidMatch=html.match(/confirm=([0-9A-Za-z_\-]+)/);if(uuidMatch)confirmUrl=baseUrl+'&confirm='+uuidMatch[1];}
    if(!confirmUrl)confirmUrl=baseUrl+'&confirm=t';
    res=await axios.get(confirmUrl,{responseType:'arraybuffer',maxRedirects:10,timeout:30000,headers:hdrs()}); parseCookies(res.headers); buf=Buffer.from(res.data); ct=res.headers['content-type']||'';
  }
  if(!ct.includes('pdf')&&!buf.slice(0,5).toString('ascii').startsWith('%PDF')) throw new Error('Google Drive did not return a PDF (size: '+buf.length+')');
  if(buf.length>50*1048576) throw new Error('File too large for Telegram (>50MB)');
  return buf;
}
async function downloadAnyPdf(url) {
  const gdMatch=url.match(/[?&]id=([a-zA-Z0-9_\-]+)/);
  if(url.includes('drive.google.com')&&gdMatch){const buf=await downloadGoogleDrive(gdMatch[1]);return{buf,serverFilename:null};}
  let cookies='';
  try{const r=await axios.get('https://govdoc.lk/',{headers:{'User-Agent':'Mozilla/5.0'},timeout:5000});cookies=(r.headers['set-cookie']||[]).join('; ');}catch(_){}
  const hdrs={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',Cookie:cookies,Referer:'https://govdoc.lk/',Accept:'application/pdf,text/html,*/*'};
  let res=await axios.get(url,{responseType:'arraybuffer',maxRedirects:10,timeout:20000,headers:hdrs});
  let buf=Buffer.from(res.data),ct=res.headers['content-type']||'';
  if(ct.includes('text/html')){const $=cheerio.load(buf.toString('utf8'));let link=$("a[href*='.pdf']").attr('href')||$("a[href*='downloadFile']").attr('href')||$("a[href*='download']").attr('href');if(!link)throw new Error('No PDF link found in response page');link=link.startsWith('http')?link:'https://govdoc.lk'+(link.startsWith('/')?'':'/')+link;res=await axios.get(link,{responseType:'arraybuffer',maxRedirects:10,timeout:20000,headers:Object.assign({},hdrs,{Accept:'application/pdf'})});buf=Buffer.from(res.data);ct=res.headers['content-type']||'';}
  if(!ct.includes('pdf')&&!buf.slice(0,5).toString('ascii').startsWith('%PDF')) throw new Error('Not a valid PDF');
  if(buf.length>50*1048576) throw new Error('File too large for Telegram');
  const cd=res.headers['content-disposition']||'',m=cd.match(/filename[^;=\n]*=["'\s]*([^\"'\n;]+)/i);
  return{buf,serverFilename:(m&&m[1].trim())||null};
}
async function downloadGovPdf(url){const{buf}=await downloadAnyPdf(url);return buf;}

async function doPaperDownload(chatId, msgId, data, from) {
  const id=data.replace('download_',''), cached=resultCache.get(id);
  if(!cached){await sendMsg(chatId,box('Expired','❌ Link expired. Please search again.'),kbMain());return;}
  await sendAdThenDownload(chatId, async()=>{
    const lm=await sendMsg(chatId,'📥 Downloading paper... please wait.');
    try{
      const links=(cached.allLinks&&cached.allLinks.length)?cached.allLinks:[cached.url]; let buf=null,lastErr=null;
      for(const link of links){try{const r=await downloadAnyPdf(link);buf=r.buf;break;}catch(e){lastErr=e;}}
      if(!buf) throw lastErr||new Error('All download links failed');
      await safeDelete(chatId,lm.message_id); await safeDelete(chatId,msgId);
      const safeTitle=String(cached.title||'SL_pastpaper_bot').replace(/[/\\:*?"<>|]/g,'_').replace(/\s+/g,' ').trim().slice(0,100);
      const srcLabel=String(cached.source||'').charAt(0).toUpperCase()+String(cached.source||'').slice(1);
      await bot.sendDocument(chatId,buf,{filename:safeTitle+'.pdf',caption:pdfCaption(cached.title,[{label:'📦 Size   :',value:(buf.length/1048576).toFixed(2)+' MB'},{label:'🌐 Source :',value:srcLabel},'─────────────────────','🎓  Good luck with your studies!']),parse_mode:'HTML'});
      resultCache.del(id); if(from) await notifyAdminDownload(from,cached.title,srcLabel);
    }catch(e){await safeDelete(chatId,lm.message_id);await sendPhoto(chatId,BOT_IMG,box('Download Error','❌ <b>Failed:</b> '+esc(e.message)+'\n\nManual: '+esc((resultCache.get(id)&&resultCache.get(id).url)||'unavailable')),kbBack());}
  });
}
async function doYearSelection(chatId, msgId, data, from) {
  const id=data.replace('year_','');
  await sendAdThenDownload(chatId, async()=>{
    const lm=await sendMsg(chatId,'📥 Downloading paper... please wait.');
    try{
      const info=yearCache.get(id); if(!info) throw new Error('Session expired. Search again.');
      const buf=await downloadGovPdf(info.downloadLink);
      const safeSub=String(info.subject).replace(/[\\/:*?"<>|]/g,'_').replace(/\s+/g,' ').trim().slice(0,80);
      await safeDelete(chatId,lm.message_id); await safeDelete(chatId,msgId);
      await bot.sendDocument(chatId,buf,{filename:(safeSub+' '+info.year).trim()+'.pdf',caption:pdfCaption(info.subject+' — '+info.year,[{label:'📦 Size   :',value:(buf.length/1048576).toFixed(2)+' MB'},{label:'🌐 Source :',value:'Government Archive'},'─────────────────────','🎓  Good luck with your studies!']),parse_mode:'HTML'});
      yearCache.del(id); if((info._from||from)) await notifyAdminDownload(info._from||from,info.subject+' '+info.year,'Government Archive');
    }catch(e){await safeDelete(chatId,lm.message_id);await sendPhoto(chatId,BOT_IMG,box('Download Error','❌ <b>Failed:</b> '+esc(e.message)+'\n\nManual: '+esc((yearCache.get(id)&&yearCache.get(id).downloadLink)||'unavailable')),kbBack());}
  });
}

// ══════════════════════════════════════════════
//  NOTES
// ══════════════════════════════════════════════
function findNotes(text) {
  const matches=[]; if(!fs.existsSync(DATA_DIR)) return matches;
  try { fs.readdirSync(DATA_DIR).filter(f=>{try{return fs.statSync(path.join(DATA_DIR,f)).isDirectory()&&f!=='countdown';}catch(_){return false;}}).forEach(sub=>{try{fs.readdirSync(path.join(DATA_DIR,sub)).filter(f=>f.endsWith('.json')).forEach(file=>{try{const d=JSON.parse(fs.readFileSync(path.join(DATA_DIR,sub,file)));if(typeof d.autoSendName==='string'&&d.autoSendName.toLowerCase()===text.toLowerCase())matches.push(Object.assign({},d,{subject:sub,_file:file}));}catch(_){}});}catch(_){}});}catch(_){}
  return matches;
}
async function showNotePage(chatId, qKey, page, originalText) {
  const PER_PAGE=10, hits=resultCache.get('noteq_'+qKey);
  if(!hits) return sendMsg(chatId,box('Session Expired','❌ Session expired. Please type the note name again.'),kbMain());
  const total=Math.ceil(hits.length/PER_PAGE), start=(page-1)*PER_PAGE;
  const kb=hits.slice(start,start+PER_PAGE).map(n=>{const h=sid(n._file+n.subject+(n.url||''));resultCache.set('note_'+h,n);return[{text:'📄 '+((n.description||n.autoSendName)+'  ['+n.subject+']').slice(0,48),callback_data:'note_send_'+h}];});
  const navRow=[];
  if(page>1)     navRow.push({text:'◀️ Prev',callback_data:'notepage_'+(page-1)+'_'+qKey});
  if(page<total) navRow.push({text:'Next ▶️',callback_data:'notepage_'+(page+1)+'_'+qKey});
  if(navRow.length) kb.push(navRow);
  kb.push([{text:'🏠 Main Menu',callback_data:'main_menu'}]);
  await sendMsg(chatId,box('Notes: "'+esc(originalText||(hits[0]&&hits[0].autoSendName)||'')+'"','📚 Found <b>'+hits.length+'</b> notes\n📄 Page <b>'+page+'</b> of <b>'+total+'</b>\n\nSelect the note to send:'),{inline_keyboard:kb});
}
async function deliverNote(chatId, note) {
  const ext=(note.url.split('.').pop()||'').toLowerCase();
  const pdfName=note.description.replace(/[\\/:*?"<>|]/g,'_').replace(/\s+/g,' ').trim().slice(0,100);
  const caption=pdfCaption(note.description,[{label:'📚 Subject :',value:note.subject},{label:'📝 Desc    :',value:note.description}]);
  try{
    if(ext==='jpg'||ext==='jpeg'||ext==='png') await bot.sendPhoto(chatId,note.url,{caption,parse_mode:'HTML'});
    else if(ext==='pdf') await bot.sendDocument(chatId,note.url,{filename:pdfName+'.pdf',caption,parse_mode:'HTML'});
    else if(ext==='mp3') await bot.sendAudio(chatId,note.url,{caption,parse_mode:'HTML'});
    else await sendMsg(chatId,caption+'\n\n🔗 '+esc(note.url));
  }catch(e){await sendMsg(chatId,box('Error','❌ Failed to send note: '+esc(e.message)));}
}

// ══════════════════════════════════════════════
//  RESULT CARD FEATURE
// ══════════════════════════════════════════════
const pdfCache = new Map();

async function loadBotLogo() {
  try { const res=await axios.get('https://files.catbox.moe/ne3rqr.jpg',{responseType:'arraybuffer',timeout:8000,headers:{'User-Agent':'Mozilla/5.0'}}); return await loadImage(Buffer.from(res.data)); }
  catch(e){ console.warn('[loadBotLogo] failed:', e.message); return null; }
}

async function fetchALResult(index, retryCount=0) {
  const BASE='https://results.exams.gov.lk', UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36';
  let cookieStr='';
  try { const r1=await axios.get(BASE+'/viewresultsforexam.htm',{headers:{'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,*/*;q=0.8','Accept-Language':'en-US,en;q=0.5','Connection':'keep-alive'},timeout:15000,maxRedirects:5}); cookieStr=(r1.headers['set-cookie']||[]).map(c=>c.split(';')[0]).join('; '); } catch(e){ console.warn('[fetchALResult] cookie warn:',e.message); }
  const body=new URLSearchParams({examSessionId:'667',year:'2025',typeTitle:'G.C.E. (A/L) Examination - 2025',isAddIndexNeeded:'N',additionalFieldName:'',comment:'Check',indexNumber:String(index)});
  let r2;
  try {
    r2=await axios.post(BASE+'/viewresults.htm',body.toString(),{headers:{'User-Agent':UA,'Content-Type':'application/x-www-form-urlencoded','Referer':BASE+'/viewresultsforexam.htm','Origin':BASE,'Accept':'text/html,application/xhtml+xml,*/*;q=0.8','Accept-Language':'en-US,en;q=0.5','Connection':'keep-alive','Cookie':cookieStr},timeout:20000,maxRedirects:5});
  } catch(e){
    const isNetErr=e.message.includes('socket')||e.message.includes('ECONNRESET')||e.message.includes('ETIMEDOUT')||e.message.includes('ECONNREFUSED');
    if(isNetErr&&retryCount<3){console.log(`[fetchALResult] retry ${retryCount+1}/3...`);await new Promise(r=>setTimeout(r,2000));return fetchALResult(index,retryCount+1);}
    throw e;
  }
  const html=typeof r2.data==='string'?r2.data:String(r2.data);
  if(!html||!html.includes('Index Number')) return{error:true};
  const $=cheerio.load(html);
  function getValue(label){let value='N/A';$('td').each((_,el)=>{if($(el).text().trim()===label){const v=$(el).next().next().text().trim();if(v){value=v;return false;}}});return value;}
  const result={name:getValue('Name'),index:getValue('Index Number'),nic:getValue('NIC Number'),stream:getValue('Subject Stream'),zscore:getValue('Z - Score'),district:getValue('District Rank'),island:getValue('Island Rank'),subjects:[]};
  const seen=new Set();
  $('table tr').each((_,el)=>{const tds=$(el).find('td');if(tds.length===2){const name=$(tds[0]).text().trim(),grade=$(tds[1]).text().trim();if(name&&grade&&name!=='Subject'&&name!=='Results'&&name.length<60&&!seen.has(name)){seen.add(name);result.subjects.push({name,grade});}}});
  pdfCache.set(String(index),result);
  return result;
}

async function generateResultCard(result) {
  try {
    const W=960,H=620,canvas=createCanvas(W,H),ctx=canvas.getContext('2d');
    const logo=await loadBotLogo();
    function drawLogo(cx,cy,r){if(!logo)return;ctx.save();ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.clip();ctx.drawImage(logo,cx-r,cy-r,r*2,r*2);ctx.restore();}
    ctx.fillStyle='#f0f4ff';ctx.fillRect(0,0,W,H);
    ctx.fillStyle='rgba(59,130,246,0.07)';
    for(let x=40;x<W;x+=40)for(let y=40;y<H;y+=40){ctx.beginPath();ctx.arc(x,y,1.5,0,Math.PI*2);ctx.fill();}
    const accent=ctx.createLinearGradient(0,0,W,0);accent.addColorStop(0,'#1d4ed8');accent.addColorStop(0.5,'#7c3aed');accent.addColorStop(1,'#0891b2');
    ctx.fillStyle=accent;ctx.fillRect(0,0,W,7);
    ctx.fillStyle='white';ctx.strokeStyle='#dbeafe';ctx.lineWidth=1.5;ctx.shadowColor='rgba(59,130,246,0.08)';ctx.shadowBlur=16;
    ctx.beginPath();ctx.roundRect(20,16,W-40,96,14);ctx.fill();ctx.stroke();ctx.shadowBlur=0;
    ctx.fillStyle='#1d4ed8';ctx.beginPath();ctx.arc(62,64,26,0,Math.PI*2);ctx.fill();drawLogo(62,64,24);
    ctx.font='13px sans-serif';ctx.fillStyle='#6b7280';ctx.textAlign='left';ctx.fillText('DEPARTMENT OF EXAMINATIONS — SRI LANKA',102,50);
    ctx.font='bold 22px sans-serif';ctx.fillStyle='#1e3a8a';ctx.fillText('G.C.E. (A/L) EXAMINATION 2025',102,76);
    ctx.font='11px sans-serif';ctx.fillStyle='#9ca3af';ctx.fillText('OFFICIAL RESULT STATEMENT',102,97);
    ctx.fillStyle='#eff6ff';ctx.strokeStyle='#93c5fd';ctx.lineWidth=1.5;
    ctx.beginPath();ctx.roundRect(W-226,36,206,36,18);ctx.fill();ctx.stroke();
    ctx.font='bold 14px sans-serif';ctx.fillStyle='#1d4ed8';ctx.textAlign='center';ctx.fillText('INDEX  '+result.index,W-123,60);
    ctx.textAlign='left';ctx.font='bold 28px sans-serif';ctx.fillStyle='#111827';
    const dname=result.name.length>36?result.name.slice(0,35)+'…':result.name;ctx.fillText(dname,30,152);
    const nw=ctx.measureText(dname).width;ctx.fillStyle='#3b82f6';ctx.fillRect(30,158,nw,2.5);
    ctx.font='13px sans-serif';ctx.fillStyle='#6b7280';ctx.fillText('NIC: '+result.nic+'   •   Stream: '+result.stream,30,178);
    const stats=[{label:'Z - SCORE',value:result.zscore,color:'#3b82f6',border:'#bfdbfe',x:30},{label:'DISTRICT RANK',value:result.district,color:'#7c3aed',border:'#ddd6fe',x:360},{label:'ISLAND RANK',value:result.island,color:'#0891b2',border:'#a5f3fc',x:690}];
    for(const s of stats){ctx.fillStyle='white';ctx.strokeStyle=s.border;ctx.lineWidth=1.5;ctx.shadowColor='rgba(0,0,0,0.06)';ctx.shadowBlur=10;ctx.beginPath();ctx.roundRect(s.x,196,254,72,12);ctx.fill();ctx.stroke();ctx.shadowBlur=0;ctx.fillStyle=s.color;ctx.beginPath();ctx.roundRect(s.x,204,4,56,2);ctx.fill();ctx.font='bold 9px sans-serif';ctx.fillStyle=s.color;ctx.textAlign='left';ctx.fillText(s.label,s.x+18,218);ctx.font='bold 30px sans-serif';ctx.fillStyle='#1e3a8a';ctx.fillText(s.value,s.x+18,252);}
    ctx.font='bold 9px sans-serif';ctx.fillStyle='#9ca3af';ctx.textAlign='left';ctx.fillText('SUBJECT RESULTS',30,296);ctx.fillStyle='#bfdbfe';ctx.fillRect(30,302,W-60,1.5);
    const GC={A:'#22c55e',B:'#3b82f6',C:'#f59e0b',S:'#a78bfa',F:'#ef4444'};
    const GB={A:'#f0fdf4',B:'#eff6ff',C:'#fffbeb',S:'#f5f3ff',F:'#fef2f2'};
    const GE={A:'#86efac',B:'#93c5fd',C:'#fcd34d',S:'#c4b5fd',F:'#fca5a5'};
    const GL={A:'DISTINCTION',B:'MERIT',C:'CREDIT',S:'SIMPLE PASS',F:'FAIL'};
    const subs=result.subjects||[],bW=440,bH=50,gX=30,gY=10;
    for(let i=0;i<Math.min(subs.length,6);i++){
      const col=i%2,row=Math.floor(i/2),bx=30+col*(bW+gX),by=310+row*(bH+gY),s=subs[i];
      const gc=GC[s.grade]||'#6b7280',gbg=GB[s.grade]||'#f9fafb',gbe=GE[s.grade]||'#d1d5db',gl=GL[s.grade]||'';
      ctx.fillStyle='white';ctx.strokeStyle=gbe;ctx.lineWidth=1;ctx.shadowColor='rgba(0,0,0,0.04)';ctx.shadowBlur=8;ctx.beginPath();ctx.roundRect(bx,by,bW,bH,9);ctx.fill();ctx.stroke();ctx.shadowBlur=0;
      ctx.fillStyle=gc;ctx.beginPath();ctx.roundRect(bx,by+10,3,bH-20,2);ctx.fill();
      ctx.font='13px sans-serif';ctx.fillStyle='#374151';ctx.textAlign='left';ctx.fillText(s.name.length>34?s.name.slice(0,33)+'…':s.name,bx+18,by+21);
      ctx.font='10px sans-serif';ctx.fillStyle='#9ca3af';ctx.fillText(gl,bx+18,by+38);
      const badgeW=s.grade.length>1?44:34;ctx.fillStyle=gbg;ctx.strokeStyle=gbe;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(bx+bW-badgeW-8,by+11,badgeW,28,7);ctx.fill();ctx.stroke();
      ctx.font='bold 16px sans-serif';ctx.fillStyle=gc;ctx.textAlign='center';ctx.fillText(s.grade,bx+bW-badgeW/2-8,by+30);
    }
    ctx.fillStyle='#1e3a8a';ctx.fillRect(0,H-54,W,10);ctx.beginPath();ctx.roundRect(0,H-48,W,48,[0,0,12,12]);ctx.fill();
    ctx.fillStyle='#3b82f6';ctx.beginPath();ctx.arc(32,H-24,14,0,Math.PI*2);ctx.fill();drawLogo(32,H-24,13);
    ctx.font='11px sans-serif';ctx.fillStyle='#93c5fd';ctx.textAlign='left';ctx.fillText('Powered by  @SL_pastpaper_bot   •   results.exams.gov.lk   •   Not an official document',54,H-18);
    ctx.fillStyle=accent;ctx.fillRect(0,H-5,W,5);
    return canvas.toBuffer('image/png');
  } catch(e){console.error('[generateResultCard]',e.message);return null;}
}

async function generateResultPDF(result) {
  return new Promise(async(resolve,reject)=>{
    try {
      const imgBuf=await generateResultCard(result);
      const doc=new PDFDocument({size:[960,620],margin:0}),chunks=[];
      doc.on('data',chunk=>chunks.push(chunk));doc.on('end',()=>resolve(Buffer.concat(chunks)));doc.on('error',reject);
      if(imgBuf){doc.image(imgBuf,0,0,{width:960,height:620});}
      else{
        doc.rect(0,0,960,620).fill('#f0f4ff');
        doc.fillColor('#1e3a8a').fontSize(28).font('Helvetica-Bold').text('G.C.E. (A/L) 2025 — RESULT',40,40);
        doc.fillColor('#111827').fontSize(18).text(result.name,40,90);
        doc.fillColor('#6b7280').fontSize(13).text(`Index: ${result.index}   NIC: ${result.nic}   Stream: ${result.stream}`,40,120);
        doc.fillColor('#1e3a8a').fontSize(16).font('Helvetica-Bold').text(`Z-Score: ${result.zscore}   District: ${result.district}   Island: ${result.island}`,40,160);
        doc.fillColor('#374151').fontSize(13).font('Helvetica').text('Subjects:',40,210);
        let sy=232;for(const s of result.subjects){doc.text(`  ${s.name}  —  ${s.grade}`,40,sy);sy+=22;}
        doc.fillColor('#6b7280').fontSize(11).text('Powered by @SL_pastpaper_bot  •  results.exams.gov.lk  •  Not an official document',40,580);
      }
      doc.end();
    }catch(e){reject(e);}
  });
}

// ══════════════════════════════════════════════
//  /result & /results COMMANDS
// ══════════════════════════════════════════════
bot.onText(/\/result(?!\w)(?:\s+(\d+))?/, async(msg,match)=>{
  const chatId=msg.chat.id,index=match&&match[1]?match[1].trim():null;
  if(!index){return sendMsg(chatId,'📋 <b>Command:</b> <code>/result &lt;index_number&gt;</code>\n\n📌 <b>Example:</b> <code>/result 5417930</code>\n\n📦 Bulk check: <code>/results 547930 5419831</code>');}
  const lm=await sendMsg(chatId,'🔍 <b>Result fetch කරමින්...</b> <code>'+esc(index)+'</code> ⏳');
  try{
    const result=await fetchALResult(index);
    await safeDelete(chatId,lm.message_id);
    if(!result||result.error){return sendMsg(chatId,'❌ Index <code>'+esc(index)+'</code> ගේ result හමු නොවිණ.\n\n⚠️ Index number නිවැරදිදැයි confirm කරන්න.');}
    const lm2=await sendMsg(chatId,'🎨 <b>Result card generate කරමින්...</b> ⏳');
    const imgBuf=await generateResultCard(result);
    await safeDelete(chatId,lm2.message_id);
    const subjectLines=(result.subjects||[]).map(s=>'  • '+esc(s.name)+' — <b>'+esc(s.grade)+'</b>').join('\n');
    const caption=
      '🎓 <b>G.C.E. (A/L) 2025 — Result</b>\n\n'+
      '👤 <b>'+esc(result.name)+'</b>\n'+
      '🆔 Index: <tg-spoiler>'+esc(result.index)+'</tg-spoiler>\n'+
      '🪪 NIC: <tg-spoiler>'+esc(result.nic)+'</tg-spoiler>\n'+
      '📚 Stream: <b>'+esc(result.stream)+'</b>\n\n'+
      '📊 Z-Score: <code>'+esc(result.zscore)+'</code>\n'+
      '🏘️ District: <b>'+esc(result.district)+'</b>\n'+
      '🏆 Island: <b>'+esc(result.island)+'</b>\n\n'+
      '📋 <b>Subjects:</b>\n'+subjectLines+'\n\n'+
      '🤖 <i>Powered by @SL_pastpaper_bot</i>';
    const kb={ inline_keyboard:[[{text:'📄 Download PDF',callback_data:'pdf_'+result.index}],[{text:'🔍 Check Another',callback_data:'result_again'}]] };
    if(imgBuf) await bot.sendPhoto(chatId,imgBuf,{caption,parse_mode:'HTML',reply_markup:kb});
    else await sendMsg(chatId,caption,kb);
  }catch(e){
    await safeDelete(chatId,lm.message_id);
    console.error('[result cmd]',e.message);
    await sendMsg(chatId,'❌ <b>Error:</b> <code>'+esc(e.message)+'</code>\n\nRetry කරන්න.');
  }
});

bot.onText(/\/results (.+)/, async(msg,match)=>{
  const chatId=msg.chat.id,raw=match[1].trim();
  const indexes=[...new Set(raw.split(/\s+/).filter(x=>/^\d+$/.test(x)))].slice(0,10);
  if(!indexes.length){return sendMsg(chatId,'📋 <b>Bulk Command:</b>\n<code>/results 5419980 5419731 5419832</code>\n\n⚠️ Numbers only, space separated, max 10.');}
  const lm=await sendMsg(chatId,'🔍 <b>Bulk check — '+indexes.length+' results fetch කරමින්...</b> ⏳\n\n'+indexes.map((idx,i)=>`${i+1}. <code>${esc(idx)}</code> ⌛`).join('\n'));
  const results=[];
  for(let i=0;i<indexes.length;i++){
    const idx=indexes[i];
    try{const r=await fetchALResult(idx);results.push({index:idx,data:r});}
    catch(e){results.push({index:idx,data:{error:true}});}
    try{
      await bot.editMessageText(
        '🔍 <b>Bulk check — '+indexes.length+' results fetch කරමින්...</b>\n\n'+
        indexes.map((x,j)=>{if(j<i+1){const r=results[j];return r.data&&!r.data.error?`${j+1}. <code>${esc(x)}</code> ✅ ${esc(r.data.name)}`:`${j+1}. <code>${esc(x)}</code> ❌ Not found`;}return`${j+1}. <code>${esc(x)}</code> ⌛`;}).join('\n'),
        {chat_id:chatId,message_id:lm.message_id,parse_mode:'HTML'});
    }catch(_){}
    if(i<indexes.length-1) await new Promise(r=>setTimeout(r,1000));
  }
  await safeDelete(chatId,lm.message_id);
  const successList=results.filter(r=>r.data&&!r.data.error),failList=results.filter(r=>!r.data||r.data.error);
  let summary='📊 <b>Bulk Result Summary</b>\n━━━━━━━━━━━━━━━━━━━━\n✅ Found: <b>'+successList.length+'</b>   ❌ Not found: <b>'+failList.length+'</b>\n\n';
  for(const r of successList){
    const d=r.data,subStr=(d.subjects||[]).map(s=>`${esc(s.name)}: <b>${esc(s.grade)}</b>`).join(' | ');
    summary+=`👤 <b>${esc(d.name)}</b>\n🆔 <tg-spoiler>${esc(d.index)}</tg-spoiler>  📚 ${esc(d.stream)}\n📊 Z: <code>${esc(d.zscore)}</code>  🏘️ D: <b>${esc(d.district)}</b>  🏆 I: <b>${esc(d.island)}</b>\n📋 ${subStr}\n━━━━━━━━━━━━━━━━━━━━\n`;
  }
  if(failList.length>0) summary+='\n❌ <b>Not found:</b> '+failList.map(r=>`<code>${esc(r.index)}</code>`).join(', ');
  summary+='\n🤖 <i>Powered by @SL_pastpaper_bot</i>';
  await sendMsg(chatId,summary);
  for(const r of successList){
    const d=r.data;
    try{
      const imgBuf=await generateResultCard(d);
      const subjectLines=(d.subjects||[]).map(s=>'  • '+esc(s.name)+' — <b>'+esc(s.grade)+'</b>').join('\n');
      const caption=
        '🎓 <b>G.C.E. (A/L) 2025 — Result</b>\n\n'+
        '👤 <b>'+esc(d.name)+'</b>\n'+
        '🆔 Index: <tg-spoiler>'+esc(d.index)+'</tg-spoiler>\n'+
        '🪪 NIC: <tg-spoiler>'+esc(d.nic)+'</tg-spoiler>\n'+
        '📚 Stream: <b>'+esc(d.stream)+'</b>\n\n'+
        '📊 Z-Score: <code>'+esc(d.zscore)+'</code>\n'+
        '🏘️ District: <b>'+esc(d.district)+'</b>\n'+
        '🏆 Island: <b>'+esc(d.island)+'</b>\n\n'+
        '📋 <b>Subjects:</b>\n'+subjectLines+'\n\n'+
        '🤖 <i>Powered by @SL_pastpaper_bot</i>';
      const kb={ inline_keyboard:[[{text:'📄 Download PDF',callback_data:'pdf_'+d.index}]] };
      if(imgBuf) await bot.sendPhoto(chatId,imgBuf,{caption,parse_mode:'HTML',reply_markup:kb});
      else await sendMsg(chatId,caption,kb);
      await new Promise(r=>setTimeout(r,500));
    }catch(e){console.error('[bulk card]',e.message);}
  }
});

// ══════════════════════════════════════════════
//  CLEANUP & GROUP EVENTS
// ══════════════════════════════════════════════
setInterval(()=>{
  const now=Date.now();
  ethCache.categories.forEach((v,k)=>{if(now-v.ts>ETH_TTL)ethCache.categories.delete(k);});
  ethCache.papers.forEach((v,k)=>{if(now-v.ts>ETH_TTL)ethCache.papers.delete(k);});
  if(ethCache.pdfs.size>1000)ethCache.pdfs.clear();
},3600000);

bot.on('polling_error',e=>console.error('[polling_error]',e.message));

bot.on('my_chat_member', async(update)=>{
  try{
    const chat=update.chat,from=update.from;
    const newStatus=update.new_chat_member&&update.new_chat_member.status;
    const oldStatus=update.old_chat_member&&update.old_chat_member.status;
    if((newStatus==='member'||newStatus==='administrator')&&(oldStatus==='left'||oldStatus==='kicked')){
      const groupName=esc(chat.title||'Unknown Group'),groupId=chat.id;
      const addedBy=from?[from.first_name,from.last_name].filter(Boolean).join(' '):'Unknown';
      const adderUser=from&&from.username?'@'+from.username:'N/A';
      await bot.sendMessage(ADMIN_GROUP,'➕ <b>Bot Added to Group!</b>\n━━━━━━━━━━━━━━━━━━━━━\n👥 <b>Group:</b> '+groupName+'\n🆔 <b>Group ID:</b> <code>'+groupId+'</code>\n📂 <b>Type:</b> '+esc(chat.type)+'\n👤 <b>Added by:</b> '+esc(addedBy)+'\n🔗 <b>Username:</b> '+esc(adderUser)+'\n📅 <b>Time (SLT):</b> '+slDateStr(new Date())+' '+slTimeStr(new Date())+'\n🤖 <b>Bot Status:</b> '+esc(newStatus)+'\n\n💡 <i>Use /chat on in that group to enable bot responses.</i>',{parse_mode:'HTML'});
      await bot.sendMessage(groupId,'👋 <b>Hello! SL_pastpaper_bot joined the group!</b>\n\n📚 Sri Lanka A/L students ට past papers, AI assistant සහ exam countdown provide කරනවා.\n\n▶️ Bot enable කරන්න: <code>/chat on</code>\n❓ Commands: <code>/wiki</code> <code>/di</code> <code>/pp</code> <code>/ai</code> <code>/eth</code> <code>/countdown</code>\n💬 Support: @SL_pastpaper_support',{parse_mode:'HTML'});
    }
    if(newStatus==='left'||newStatus==='kicked'){
      const groupName=esc(chat.title||'Unknown Group');
      const removedBy=from?[from.first_name,from.last_name].filter(Boolean).join(' '):'Unknown';
      const removerUser=from&&from.username?'@'+from.username:'N/A';
      if(groupChatsDB[String(chat.id)]){delete groupChatsDB[String(chat.id)];saveGroupChats();}
      await bot.sendMessage(ADMIN_GROUP,'➖ <b>Bot Removed from Group!</b>\n━━━━━━━━━━━━━━━━━━━━━\n👥 <b>Group:</b> '+groupName+'\n🆔 <b>Group ID:</b> <code>'+chat.id+'</code>\n👤 <b>Removed by:</b> '+esc(removedBy)+'\n🔗 <b>Username:</b> '+esc(removerUser)+'\n📅 <b>Time (SLT):</b> '+slDateStr(new Date())+' '+slTimeStr(new Date()),{parse_mode:'HTML'});
    }
  }catch(e){console.error('[my_chat_member]',e.message);}
});

// ══════════════════════════════════════════════
//  STARTUP
// ══════════════════════════════════════════════
async function loadPdfThumb() {
  try{const res=await axios.get(PDF_THUMB_URL,{responseType:'arraybuffer',timeout:10000});PDF_THUMB_BUF=Buffer.from(res.data);console.log('  🖼️  PDF thumbnail loaded:',PDF_THUMB_BUF.length,'bytes');}
  catch(e){console.warn('  ⚠️  PDF thumbnail load failed:',e.message);PDF_THUMB_BUF=null;}
}

restoreCountdownJobs();
loadPdfThumb();

console.log('\n  ╔══════════════════════════════════════════════╗');
console.log('  ║     SL_pastpaper_bot  v5.1  (fixed)          ║');
console.log('  ║  Inline Search · Group DM · Join Check       ║');
console.log('  ║  Educational AI · Image AI · AI Modes        ║');
console.log('  ║  A/L 2025 Results · Bulk Results             ║');
console.log('  ╚══════════════════════════════════════════════╝\n');
console.log('  👥 Users loaded:', Object.keys(usersDB).length);
console.log('  🤖 AI: Educational AI + chai2 + Claude Haiku fallback');
console.log('  📅 Countdown jobs restoring...\n');
