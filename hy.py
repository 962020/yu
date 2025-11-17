import tkinter
import webbrowser
from tkinter import PhotoImage, messagebox


class VIPVideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title('VIP追剧神器')
        self.root.geometry('480x380')  # 调整窗口高度适配图片
        self.create_widgets()

    def create_widgets(self):
        # 输入区域
        label_movie_link = tkinter.Label(self.root, text='输入视频网址：')
        label_movie_link.place(x=20, y=20, width=100, height=30)

        self.entry_movie_link = tkinter.Entry(self.root)
        self.entry_movie_link.place(x=125, y=20, width=260, height=30)

        button_movie_link = tkinter.Button(self.root, text='清空', command=self.empty)
        button_movie_link.place(x=400, y=20, width=50, height=30)

        # 平台按钮
        platforms = [
            ('爱奇艺', self.open_iqy, 25),
            ('腾讯视频', self.open_tx, 125),
            ('优酷视频', self.open_yq, 225)
        ]
        for text, command, xpos in platforms:
            tkinter.Button(self.root, text=text, command=command)\
                .place(x=xpos, y=60, width=80, height=40)

        # 播放按钮
        tkinter.Button(self.root, text='播放VIP视频', command=self.play_video)\
            .place(x=325, y=60, width=125, height=40)

        # 文字提示
        tkinter.Label(self.root,
                    text='乔乔制作，请勿用于商业用途！',
                    fg='black',
                    font=('微软雅黑', 12, 'bold'))\
            .place(x=20, y=110, width=440, height=25)

    # 添加缺失的方法
    def empty(self):
        """清空输入框"""
        self.entry_movie_link.delete(0, tkinter.END)

    def open_iqy(self):
        """打开爱奇艺"""
        webbrowser.open('https://www.iqiyi.com')

    def open_tx(self):
        """打开腾讯视频"""
        webbrowser.open('https://v.qq.com')

    def open_yq(self):
        """打开优酷视频"""
        webbrowser.open('https://www.youku.com/')

    def play_video(self):
        """播放VIP视频"""
        video_url = self.entry_movie_link.get().strip()
        if video_url:
            play_url = f'https://jx.xmflv.cc/?url={video_url}'
            webbrowser.open(play_url)
        else:
            # 创建一个简单的提示窗口
            messagebox.showwarning("提示", "请输入视频链接！")