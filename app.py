import os,sys,subprocess,tempfile
from pathlib import Path
from PySide6.QtCore import Qt,QUrl,QThread,Signal
from PySide6.QtGui import QAction,QColor,QPalette
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from core import Project,probe_media,thumbnail,build_render_command,VIDEO_EXT,AUDIO_EXT

ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
FFMPEG=str(ROOT/'ffmpeg.exe') if (ROOT/'ffmpeg.exe').exists() else str(Path(__file__).parent/'ffmpeg.exe')

STYLE='''QWidget{background:#11131a;color:#eef1f7;font:13px "Microsoft YaHei"}QMainWindow{background:#0b0d12}QPushButton{background:#252a36;border:1px solid #39404f;border-radius:7px;padding:8px 12px}QPushButton:hover{background:#303646;border-color:#9a7cff}QPushButton#primary{background:#7655e8;border-color:#8b6df1;color:white;font-weight:600}QPushButton#danger{color:#ff9da5}QLineEdit,QTextEdit,QDoubleSpinBox,QComboBox,QSpinBox{background:#191c25;border:1px solid #343b4b;border-radius:6px;padding:7px}QListWidget{background:#151821;border:1px solid #2d3240;border-radius:8px}QListWidget::item{padding:10px;border-bottom:1px solid #272c38}QListWidget::item:selected{background:#3a2e68;border-left:3px solid #9c7cff}QGroupBox{border:1px solid #303644;border-radius:9px;margin-top:12px;padding:14px 10px 10px}QGroupBox::title{subcontrol-origin:margin;left:12px;color:#c8ccda}QTabWidget::pane{border:1px solid #303644;border-radius:8px}QTabBar::tab{background:#1a1d26;padding:9px 12px;color:#9da4b5}QTabBar::tab:selected{color:white;border-bottom:2px solid #8b6df1}QSlider::groove:horizontal{height:5px;background:#303541;border-radius:2px}QSlider::handle:horizontal{width:15px;margin:-5px 0;background:#9676f2;border-radius:7px}QProgressBar{border:0;background:#252a35;border-radius:5px;text-align:center}QProgressBar::chunk{background:#7655e8;border-radius:5px}'''

class RenderThread(QThread):
    done=Signal(bool,str);progress=Signal(int)
    def __init__(self,cmd,duration):super().__init__();self.cmd=cmd;self.duration=max(.1,duration)
    def run(self):
        p=subprocess.Popen(self.cmd,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',creationflags=0x08000000 if os.name=='nt' else 0)
        import re
        tail=[]
        for line in p.stderr:
            tail.append(line);tail=tail[-20:]
            m=re.search(r'time=(\d+):(\d+):(\d+(?:\.\d+)?)',line)
            if m:self.progress.emit(min(99,int((int(m[1])*3600+int(m[2])*60+float(m[3]))/self.duration*100)))
        code=p.wait();self.done.emit(code==0,'' if code==0 else ''.join(tail)[-1200:])

class Main(QMainWindow):
    def __init__(self):
        super().__init__();self.project=Project();self.metas={};self.render_thread=None
        self.setWindowTitle('灵剪 AI 视频编辑器 1.1');self.resize(1500,900);self.setMinimumSize(1180,720);self.build();self.shortcuts();self.statusBar().showMessage('就绪 · 第一步：点击左侧“导入素材”')
    def button(self,text,fn,primary=False):
        b=QPushButton(text);b.clicked.connect(fn)
        if primary:b.setObjectName('primary')
        return b
    def build(self):
        root=QWidget();self.setCentralWidget(root);outer=QVBoxLayout(root);outer.setContentsMargins(10,8,10,8)
        top=QHBoxLayout();top.addWidget(QLabel('<b style="font-size:19px">✦ 灵剪 AI</b>'));self.title=QLineEdit('未命名作品');self.title.setPlaceholderText('输入作品名称');self.title.setMaximumWidth(260);top.addWidget(self.title);top.addStretch();top.addWidget(self.button('打开工程',self.open_project));top.addWidget(self.button('保存 Ctrl+S',self.save_project));top.addWidget(self.button('导出 MP4',self.export,True));outer.addLayout(top)
        guide=QLabel('  ① 导入素材    →    ② 加入时间线    →    ③ 裁切、分割与字幕    →    ④ 导出 MP4');guide.setStyleSheet('background:#191d29;color:#c9c2f7;padding:9px;border-radius:7px');outer.addWidget(guide)
        split=QSplitter();outer.addWidget(split,1)
        left=QWidget();ll=QVBoxLayout(left);ll.addWidget(QLabel('<b>① 素材库</b>'));ll.addWidget(QLabel('导入后选择素材，再点击“加入时间线”'));ll.addWidget(self.button('＋ 导入素材',self.import_files,True));self.media=QListWidget();self.media.itemDoubleClicked.connect(self.add_selected);ll.addWidget(self.media);ll.addWidget(self.button('＋ 将选中视频加入时间线',self.add_current,True));split.addWidget(left)
        center=QWidget();cl=QVBoxLayout(center);cl.addWidget(QLabel('<b>预览窗口</b>'));self.video=QVideoWidget();self.video.setMinimumHeight(340);self.video.setStyleSheet('background:#050608;border-radius:9px');cl.addWidget(self.video,1);self.player=QMediaPlayer();self.audio=QAudioOutput();self.player.setVideoOutput(self.video);self.player.setAudioOutput(self.audio)
        ctl=QHBoxLayout();ctl.addWidget(self.button('▶ 播放 / 暂停  Space',self.play));self.seek=QSlider(Qt.Horizontal);self.seek.sliderMoved.connect(self.seek_to);ctl.addWidget(self.seek,1);self.time=QLabel('00:00 / 00:00');ctl.addWidget(self.time);cl.addLayout(ctl);self.player.durationChanged.connect(lambda d:self.seek.setMaximum(d));self.player.positionChanged.connect(self.position)
        tools=QHBoxLayout();tools.addWidget(QLabel('<b>② 时间线</b>'));tools.addWidget(self.button('✂ 分割  Ctrl+B',self.split_clip));tools.addWidget(self.button('← 前移',lambda:self.move_clip(-1)));tools.addWidget(self.button('后移 →',lambda:self.move_clip(1)));delete=self.button('删除  Del',self.delete_clip);delete.setObjectName('danger');tools.addWidget(delete);tools.addStretch();cl.addLayout(tools)
        self.timeline=QListWidget();self.timeline.currentRowChanged.connect(self.select_clip);self.timeline.setToolTip('点击片段后，在右侧“片段编辑”中修改');cl.addWidget(self.timeline);split.addWidget(center)
        tabs=QTabWidget();edit=QWidget();el=QVBoxLayout(edit)
        prop=QGroupBox('③ 编辑选中的片段');pf=QFormLayout(prop);self.start=QDoubleSpinBox();self.end=QDoubleSpinBox();[x.setRange(0,86400) for x in (self.start,self.end)];[x.setDecimals(2) for x in (self.start,self.end)];self.caption=QLineEdit();self.caption.setPlaceholderText('输入要显示在画面上的文字');self.pos=QComboBox();self.pos.addItem('底部','bottom');self.pos.addItem('居中','center');self.pos.addItem('顶部','top');self.trans=QComboBox();self.trans.addItem('淡入淡出','fade');self.trans.addItem('无转场','none');self.volume=QDoubleSpinBox();self.volume.setRange(0,2);self.volume.setSingleStep(.1);self.volume.setValue(1);pf.addRow('从第几秒开始',self.start);pf.addRow('到第几秒结束',self.end);pf.addRow('字幕 / 标题',self.caption);pf.addRow('字幕位置',self.pos);pf.addRow('片段转场',self.trans);pf.addRow('原声音量',self.volume);pf.addRow(self.button('✓ 应用修改',self.apply_clip,True));el.addWidget(prop);el.addStretch();tabs.addTab(edit,'片段编辑')
        ai=QWidget();al=QVBoxLayout(ai);box=QGroupBox('AI 智能初剪');af=QFormLayout(box);self.prompt=QTextEdit('剪成节奏流畅的精彩短视频，优先保留有声音且时长合适的片段。');self.prompt.setMaximumHeight(100);af.addRow('剪辑要求',self.prompt);self.target=QSpinBox();self.target.setRange(5,600);self.target.setValue(30);af.addRow('目标时长（秒）',self.target);af.addRow(self.button('✦ 生成智能初剪',self.auto_edit,True));al.addWidget(box);al.addWidget(QLabel('提示：AI 初剪后仍可回到“片段编辑”继续调整。'));al.addStretch();tabs.addTab(ai,'AI 初剪')
        output=QWidget();ol=QVBoxLayout(output);music=QGroupBox('音乐与输出');mf=QFormLayout(music);self.bgm=QLineEdit();self.bgm.setReadOnly(True);self.bgm.setPlaceholderText('未选择背景音乐');mf.addRow(self.bgm,self.button('选择音乐',self.choose_bgm));self.bgmvol=QDoubleSpinBox();self.bgmvol.setRange(0,1);self.bgmvol.setSingleStep(.05);self.bgmvol.setValue(.22);mf.addRow('音乐音量',self.bgmvol);self.ratio=QComboBox();self.ratio.addItems(['9:16 竖屏','16:9 横屏','1:1 方形']);mf.addRow('导出画幅',self.ratio);mf.addRow(self.button('④ 导出 MP4',self.export,True));ol.addWidget(music);self.progress=QProgressBar();self.progress.hide();ol.addWidget(self.progress);ol.addStretch();tabs.addTab(output,'音乐与导出');split.addWidget(tabs);split.setSizes([280,880,340])
    def shortcuts(self):
        for key,fn in [('Ctrl+S',self.save_project),('Ctrl+B',self.split_clip),('Delete',self.delete_clip),('Space',self.play)]:a=QAction(self);a.setShortcut(key);a.triggered.connect(fn);self.addAction(a)
    def alert(self,msg,err=False): (QMessageBox.critical if err else QMessageBox.information)(self,'灵剪 AI',msg)
    def import_files(self):
        files,_=QFileDialog.getOpenFileNames(self,'导入素材','','媒体文件 (*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.mp3 *.wav *.m4a *.aac *.flac *.ogg)')
        for path in files:
            try:
                if Path(path).suffix.lower() in VIDEO_EXT:
                    meta=probe_media(FFMPEG,path);self.metas[path]=meta;item=QListWidgetItem(f"🎬 {meta['name']}\n{meta['duration']:.1f}s · {'含声音' if meta['has_audio'] else '无声音'}");item.setData(Qt.UserRole,path);self.media.addItem(item)
                elif Path(path).suffix.lower() in AUDIO_EXT:self.project.bgm=path;self.bgm.setText(Path(path).name)
            except Exception as e:self.alert(str(e),True)
    def add_selected(self,item):
        p=item.data(Qt.UserRole);self.project.add(self.metas[p]);self.refresh();self.timeline.setCurrentRow(len(self.project.clips)-1)
    def add_current(self):
        item=self.media.currentItem()
        if not item:return self.alert('请先在素材库中选择一个视频。')
        self.add_selected(item)
    def refresh(self):
        self.timeline.clear()
        for i,c in enumerate(self.project.clips):self.timeline.addItem(f'{i+1:02d}  {c.name}  [{c.start:.2f}–{c.end:.2f}s]  {c.caption or ""}')
        self.statusBar().showMessage(f'{len(self.project.clips)} 个片段 · 总时长 {self.project.duration:.1f} 秒')
    def select_clip(self,row):
        if row<0 or row>=len(self.project.clips):return
        c=self.project.clips[row];self.start.setValue(c.start);self.end.setValue(c.end);self.caption.setText(c.caption);self.pos.setCurrentIndex(max(0,self.pos.findData(c.position)));self.trans.setCurrentIndex(max(0,self.trans.findData(c.transition)));self.volume.setValue(c.volume);self.player.setSource(QUrl.fromLocalFile(c.path));self.player.setPosition(int(c.start*1000))
    def play(self): self.player.pause() if self.player.playbackState()==QMediaPlayer.PlayingState else self.player.play()
    def seek_to(self,v):self.player.setPosition(v)
    def position(self,p):self.seek.setValue(p);self.time.setText(f'{p//60000:02d}:{p//1000%60:02d} / {self.player.duration()//60000:02d}:{self.player.duration()//1000%60:02d}')
    def apply_clip(self):
        r=self.timeline.currentRow()
        if r<0:return
        try:self.project.trim(r,self.start.value(),self.end.value());c=self.project.clips[r];c.caption=self.caption.text();c.position=self.pos.currentData();c.transition=self.trans.currentData();c.volume=self.volume.value();self.refresh();self.timeline.setCurrentRow(r);self.statusBar().showMessage('片段修改已应用')
        except Exception as e:self.alert(str(e),True)
    def split_clip(self):
        r=self.timeline.currentRow()
        if r<0:return
        try:self.project.split(r,self.player.position()/1000);self.refresh();self.timeline.setCurrentRow(r+1)
        except Exception as e:self.alert(str(e),True)
    def delete_clip(self):
        r=self.timeline.currentRow()
        if r>=0:self.project.delete(r);self.refresh();self.timeline.setCurrentRow(min(r,len(self.project.clips)-1))
    def move_clip(self,d):
        r=self.timeline.currentRow();n=r+d
        if r>=0 and 0<=n<len(self.project.clips):self.project.move(r,n);self.refresh();self.timeline.setCurrentRow(n)
    def auto_edit(self):
        if not self.project.clips:return self.alert('请先把视频加入时间线')
        self.project.prompt=self.prompt.toPlainText();self.project.auto_edit(self.target.value());self.refresh();self.alert(f'已生成 {self.project.duration:.1f} 秒智能初剪，可继续手动调整。')
    def choose_bgm(self):
        p,_=QFileDialog.getOpenFileName(self,'选择背景音乐','','音频 (*.mp3 *.wav *.m4a *.aac *.flac *.ogg)')
        if p:self.project.bgm=p;self.bgm.setText(Path(p).name)
    def save_project(self):
        p,_=QFileDialog.getSaveFileName(self,'保存工程',self.title.text()+'.ljproject','灵剪工程 (*.ljproject)')
        if p:self.project.title=self.title.text();self.project.bgm_volume=self.bgmvol.value();self.project.save(p);self.statusBar().showMessage('工程已保存：'+p)
    def open_project(self):
        p,_=QFileDialog.getOpenFileName(self,'打开工程','','灵剪工程 (*.ljproject)')
        if not p:return
        try:
            self.project=Project.load(p);missing=[c.path for c in self.project.clips if not Path(c.path).exists()]
            if missing:return self.alert('工程素材缺失：\n'+'\n'.join(missing[:5]),True)
            self.title.setText(self.project.title);self.prompt.setPlainText(self.project.prompt);self.bgm.setText(Path(self.project.bgm).name if self.project.bgm else '');self.bgmvol.setValue(self.project.bgm_volume);self.refresh()
        except Exception as e:self.alert('工程打开失败：'+str(e),True)
    def export(self):
        if not self.project.clips:return self.alert('时间线为空')
        p,_=QFileDialog.getSaveFileName(self,'导出 MP4',self.title.text()+'.mp4','MP4 视频 (*.mp4)')
        if not p:return
        size={'9:16 竖屏':(720,1280),'16:9 横屏':(1280,720),'1:1 方形':(1080,1080)}[self.ratio.currentText()];self.project.bgm_volume=self.bgmvol.value()
        try:cmd=build_render_command(FFMPEG,self.project,p,*size,'high')
        except Exception as e:return self.alert(str(e),True)
        self.progress.setValue(0);self.progress.show();self.render_thread=RenderThread(cmd,self.project.duration);self.render_thread.progress.connect(self.progress.setValue);self.render_thread.done.connect(lambda ok,msg:self.export_done(ok,msg,p));self.render_thread.start();self.statusBar().showMessage('正在渲染，请勿关闭程序…')
    def export_done(self,ok,msg,path):
        self.progress.setValue(100 if ok else 0);self.statusBar().showMessage('导出完成' if ok else '导出失败');self.alert(('导出完成：\n'+path) if ok else ('FFmpeg 导出失败：\n'+msg),not ok)

if __name__=='__main__':
    app=QApplication(sys.argv);app.setStyle('Fusion');app.setStyleSheet(STYLE);w=Main();w.show();sys.exit(app.exec())
