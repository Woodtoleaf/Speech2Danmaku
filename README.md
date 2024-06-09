# Speech2Danmaku
一个简单的本地中文同传字幕，用于接收麦克风的声音，并将其输出到浮动的字幕中。

基于[Whisper语音识别模型](https://github.com/shuaijiang/Whisper-Finetune/tree/master)进行了微调。

## 使用方法
提供了一个可执行的exe文件。

下载release中的zip，解压到任意目录下（最好是英文目录）。

在涉及音频整合的部分本项目需要[FFmpeg](https://ffmpeg.org/download.html)，运行前需要将其添加到系统的环境变量中。（方便一些人的使用在压缩包中默认提供了一个FFmpeg，也可以自行去官网下载）

之后直接运行解压包的exe即可。

## 可选

### 安装Nvidia CUDA Toolkit
安装[Nvidia CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)，来让模型使用GPU而不是CPU。

### 识别电脑声音
如果想使用本项目识别电脑输出的音频而不是麦克风收到的声音，需要安装[Vb Audio Vitual Cable](https://vb-audio.com/Cable/index.htm)之类的虚拟音频设备。将其设置为默认声音设备和默认麦克风，为了在自己的设备里接受同样的音频，在虚拟麦克风的属性中的侦听选项，选择对应的音频设备即可。

