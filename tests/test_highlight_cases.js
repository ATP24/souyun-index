// 测试关键词朱砂高亮各种边界情况
const path = require('path');
const htmlPath = path.resolve(__dirname, '../src/index.html');
const html = fs.readFileSync(htmlPath, 'utf8');

const scriptMatch = html.match(/function escapeHtml[\s\S]*?function highlightKeywords[\s\S]*?return safeText\.replace\(regex, '<span class="keyword-highlight">\$1<\/span>'\);\s*\}/);
if (!scriptMatch) {
    console.error('FAIL: Could not extract highlight functions from index.html');
    process.exit(1);
}

eval(scriptMatch[0]);

const cases = [
    {
        title: '纯正文名句匹配',
        text: '白日依山尽，黄河入海流。欲穷千里目，更上一层楼。',
        query: '白日依山尽',
        expected: '<span class="keyword-highlight">白日依山尽</span>，黄河入海流。欲穷千里目，更上一层楼。'
    },
    {
        title: '正文中包含逗号句号整句匹配',
        text: '明月几时有？把酒问青天。不知天上宫阙，今夕是何年。',
        query: '明月几时有？把酒问青天',
        expected: '<span class="keyword-highlight">明月几时有？把酒问青天</span>。不知天上宫阙，今夕是何年。'
    },
    {
        title: '跨空格多关键词匹配',
        text: '孤帆远影碧空尽，唯见长江天际流。',
        query: '孤帆 碧空 天际',
        check: (res) => res.includes('<span class="keyword-highlight">孤帆</span>') && res.includes('<span class="keyword-highlight">碧空</span>') && res.includes('<span class="keyword-highlight">天际</span>')
    },
    {
        title: '特殊字符转义防注入',
        text: '李白 & 杜甫 <唐代名篇>',
        query: '李白 &',
        check: (res) => !res.includes('<script>') && res.includes('&amp;')
    },
    {
        title: '空输入安全处理',
        text: '正常文本',
        query: '',
        expected: '正常文本'
    },
    {
        title: '诗歌标题书名号内匹配',
        text: '《全唐诗》卷二百三十七',
        query: '全唐诗',
        expected: '《<span class="keyword-highlight">全唐诗</span>》卷二百三十七'
    }
];

let allPassed = true;
for (const tc of cases) {
    const res = highlightKeywords(tc.text, tc.query);
    let ok = false;
    if (tc.expected) {
        ok = (res === tc.expected);
    } else if (tc.check) {
        ok = tc.check(res);
    }
    if (ok) {
        console.log('[PASS] ' + tc.title);
    } else {
        console.error('[FAIL] ' + tc.title);
        console.error('  Query:    ' + tc.query);
        console.error('  Got:      ' + res);
        console.error('  Expected: ' + tc.expected);
        allPassed = false;
    }
}

if (!allPassed) process.exit(1);
console.log('All highlight test cases passed successfully!');
