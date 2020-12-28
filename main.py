import codecs
import jieba
import jieba.posseg as pseg
from pyecharts import options as opts
from pyecharts.charts import Graph


class RelationExtractor:
    def __init__(self, stop_words, name_dicts, alias_name):
        # 人名词典
        self.name_dicts = [line.strip().split(' ')[0] for line in open(name_dicts, 'rt', encoding='utf-8').readlines()]
        # 停止词表
        self.stop_words = [line.strip() for line in open(stop_words, 'rt', encoding='utf-8').readlines()]
        # 别名词典
        self.alias_names = dict([(line.split(',')[0].strip(), line.split(',')[1].strip()) for line in
                                 open(alias_name, 'rt', encoding='utf-8').readlines()])
        # 加载词典
        jieba.load_userdict(name_dicts)

    def extract(self, text):
        # 人物关系
        relationship = {}
        # 人名频次
        name_frequency = {}
        # 每个段落中的人名
        name_in_paragraph = []

        # 读取小说文本，统计人名出现的频次，以及每个段落中出现的人名
        with codecs.open(text, "r", "gbk") as f:
            for line in f.readlines():
                poss = pseg.cut(line)

                name_in_paragraph.append([])
                for w in poss:
                    # 跳过废弃词
                    if w.word in self.stop_words:
                        continue
                    # 规范化人物姓名
                    word = w.word
                    if self.alias_names.get(word):
                        word = self.alias_names.get(word)
                    # 跳过不在人名字典
                    if word not in self.name_dicts:
                        continue
                    # 同一个段落中的人名
                    name_in_paragraph[-1].append(word)
                    if name_frequency.get(word) is None:
                        name_frequency[word] = 0
                        relationship[word] = {}
                    name_frequency[word] += 1

        # 基于共现组织人物关系
        for paragraph in name_in_paragraph:
            for name1 in paragraph:
                for name2 in paragraph:
                    if name1 == name2:
                        continue
                    if relationship[name1].get(name2) is None:
                        relationship[name1][name2] = 1
                    else:
                        relationship[name1][name2] = relationship[name1][name2] + 1

        # 返回节点和边
        return name_frequency, relationship


def export_gephi(node, relationship):
    # 输出节点
    with codecs.open("./output/node.csv", "w", "gbk") as f:
        f.write("Id Label Weight\r\n")
        for name, freq in node.items():
            f.write(name + " " + name + " " + str(freq) + "\r\n")
    # 输出边
    with codecs.open("./output/edge.csv", "w", "gbk") as f:
        f.write("Source Target Weight\r\n")
        for name, edges in relationship.items():
            for v, w in edges.items():
                if w > 0:
                    f.write(name + " " + v + " " + str(w) + "\r\n")


def export_ECharts(node, relationship):
    # 总频次，用于数据的归一化
    total = sum(list(map(lambda x: x[1], node.items())))

    # 输出节点
    nodes_data = []
    for name, freq in node.items():
        nodes_data.append(opts.GraphNode(
            name=name,
            symbol_size=round(freq / total * 100, 2),
            value=freq,
        )),

    # 输出边
    links_data = []
    for name, edges in relationship.items():
        for v, w in edges.items():
            if w > 0:
                links_data.append(opts.GraphLink(source=v, target=w, value=w))

    # 绘制Graph
    c = (
        Graph()
            .add(
            "",
            nodes_data,
            links_data,
            gravity=0.2,
            repulsion=8000,
            is_draggable=True,
            symbol='circle',
            linestyle_opts=opts.LineStyleOpts(
                curve=0.3, width=0.5, opacity=0.7
            ),
            edge_label=opts.LabelOpts(
                is_show=False, position="middle", formatter="{b}->{c}"
            ),
        )
            .set_global_opts(
            title_opts=opts.TitleOpts(title="Fate Zero Character Relationship")
        )
            .render("./result/relationship.html")
    )


if __name__ == '__main__':
    extractor = RelationExtractor(
        './input/discarded.txt',
        './input/character.txt',
        './input/alias.txt'
    )
    node, relationships = extractor.extract('./input/Fate_Zero.txt')
    export_gephi(node, relationships)
    export_ECharts(node, relationships)