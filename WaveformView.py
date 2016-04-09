#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
# generated by wxGlade 0.3.5.1 on Thu Apr 21 12:10:56 2005

# Papagayo, a lip-sync tool for use with Lost Marble's Moho
# Copyright (C) 2005 Mike Clifton
# Contact information at http://www.lostmarble.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import math
import wx

if hasattr(wx, "Color"):
    wx.Colour = wx.Color
else:
    wx.Color = wx.Colour

# begin wxGlade: dependencies
# end wxGlade

from LipsyncDoc import *

BUFFERED = 1
SIMPLE_DISPLAY = 0

defaultSampleWidth = 2
defaultSamplesPerFrame = 4
defaultSampleWidth = 4
defaultSamplesPerFrame = 2

class WaveformView(wx.ScrolledWindow):
    def __init__(self, *args, **kwds):
        # begin wxGlade: WaveformView.__init__
        kwds["style"] = wx.BORDER_SUNKEN | wx.TAB_TRAVERSAL
        wx.ScrolledWindow.__init__(self, *args, **kwds)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

        # test for wxPython type
        cdc = wx.ClientDC(self)
        self.isWxPhoenix = False
        if not "SetClippingRect" in dir(cdc):
            self.isWxPhoenix = True

        # Other initialization
        self.doc = None
        self.maxWidth = 1
        self.maxHeight = 1
        self.isDragging = False
        self.basicScrubbing = False
        self.curFrame = 0
        self.oldFrame = 0
        self.buffer = None
        self.clipRect = None
        self.sampleWidth = defaultSampleWidth
        self.samplesPerFrame = defaultSamplesPerFrame
        self.samplesPerSec = 24 * self.samplesPerFrame
        self.frameWidth = self.sampleWidth * self.samplesPerFrame
        self.phraseBottom = 16
        self.wordBottom = 32
        self.phonemeTop = 128

        # Connect event handlers
        # window events
        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_SIZE(self, self.OnSize)
        # mouse events
        wx.EVT_LEFT_DOWN(self, self.OnMouseDown)
        wx.EVT_RIGHT_DOWN(self, self.OnMouseDown)
        wx.EVT_LEFT_DCLICK(self, self.OnMouseDown)
        wx.EVT_LEFT_UP(self, self.OnMouseUp)
        wx.EVT_RIGHT_UP(self, self.OnMouseUp)
        wx.EVT_MOTION(self, self.OnMouseMove)
        wx.EVT_MOUSEWHEEL(self, self.OnMouseWheel)

        # Force an update
        self.OnSize()

    def __set_properties(self):
        # begin wxGlade: WaveformView.__set_properties
        self.SetMinSize((200,200))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.SetScrollRate(10, 0)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: WaveformView.__do_layout
        self.Layout()
        # end wxGlade

    def OnPaint(self, event):
        if BUFFERED:
            # Create a buffered paint DC.  It will create the real
            # wx.PaintDC and then blit the bitmap to it when dc is
            # deleted.  Since we don't need to draw anything else
            # here that's all there is to it.
            if self.buffer is not None:
                if 1:
                    dc = wx.BufferedPaintDC(self, self.buffer, wx.BUFFER_VIRTUAL_AREA)
                else:
                    dc = wx.BufferedPaintDC(self, self.buffer)
            else:
                event.Skip()
        else:
            dc = wx.PaintDC(self)
            self.PrepareDC(dc)
            # since we're not buffering in this case, we have to
            # paint the whole window, potentially very time consuming.
            self.Draw(dc)

    def OnSize(self, event = None):
        self.maxHeight = self.GetClientSize().height
        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        if BUFFERED:
            # Initialize the buffer bitmap.  No real DC is needed at this point.
            if self.maxWidth > 0 and self.maxHeight > 0:
                self.buffer = wx.EmptyBitmap(self.maxWidth, self.maxHeight)
            else:
                self.buffer = None
            self.UpdateDrawing()

    def OnMouseDown(self, event):
        self.isDragging = False
        self.dragChange = False
        self.draggingEnd = -1 # which end of the object (beginning or end) are you dragging
        self.selectedPhrase = None
        self.selectedWord = None
        self.selectedPhoneme = None
        x, y = event.GetPosition()
        x, y = self.CalcUnscrolledPosition(x, y)
        self.scrubFrame = x / self.frameWidth
        self.lastFrame = self.scrubFrame
        self.dragStartFrame = self.scrubFrame
        if (self.doc is not None) and (self.doc.sound is not None) and (not self.doc.sound.IsPlaying()):
            self.isDragging = True
            if self.doc.currentVoice is not None:
                # test to see if the user clicked on a phrase, word, or phoneme
                # first, find the phrase that was clicked on
                for phrase in self.doc.currentVoice.phrases:
                    if (self.scrubFrame >= phrase.startFrame) and (self.scrubFrame <= phrase.endFrame):
                        self.selectedPhrase = phrase
                # next, find the word that was clicked on
                if self.selectedPhrase is not None:
                    for word in self.selectedPhrase.words:
                        if (self.scrubFrame >= word.startFrame) and (self.scrubFrame <= word.endFrame):
                            self.selectedWord = word
                # finally, find the phoneme that was clicked on
                if self.selectedWord is not None:
                    for phoneme in self.selectedWord.phonemes:
                        if self.scrubFrame == phoneme.frame:
                            self.selectedPhoneme = phoneme

                self.parentPhrase = self.selectedPhrase
                self.parentWord = self.selectedWord

                # now, test if the click was within the vertical range of one of these objects
                if (self.selectedPhrase is not None) and (y > self.selectedPhrase.top) and (y < self.selectedPhrase.bottom):
                    self.selectedWord = None
                    self.selectedPhoneme = None
                    self.draggingEnd = 0 # beginning of phrase
                    dist = self.scrubFrame - self.selectedPhrase.startFrame
                    if (self.selectedPhrase.endFrame - self.scrubFrame) < dist:
                        self.draggingEnd = 1 # end of phrase
                        dist = self.selectedPhrase.endFrame - self.scrubFrame
                    if (self.selectedPhrase.endFrame - self.selectedPhrase.startFrame > 1) and (math.fabs((self.selectedPhrase.endFrame + self.selectedPhrase.startFrame) / 2 - self.scrubFrame) < dist):
                        self.draggingEnd = 2 # middle of phrase
                elif (self.selectedWord is not None) and (y > self.selectedWord.top) and (y < self.selectedWord.bottom):
                    self.selectedPhrase = None
                    self.selectedPhoneme = None
                    self.draggingEnd = 0 # beginning of word
                    dist = self.scrubFrame - self.selectedWord.startFrame
                    if (self.selectedWord.endFrame - self.scrubFrame) < dist:
                        self.draggingEnd = 1 # end of word
                        dist = self.selectedWord.endFrame - self.scrubFrame
                    if (self.selectedWord.endFrame - self.selectedWord.startFrame > 1) and (math.fabs((self.selectedWord.endFrame + self.selectedWord.startFrame) / 2 - self.scrubFrame) < dist):
                        self.draggingEnd = 2 # middle of word
                elif (self.selectedPhoneme is not None) and (y > self.selectedPhoneme.top) and (y < self.selectedPhoneme.bottom):
                    self.selectedPhrase = None
                    self.selectedWord = None
                    if self.scrubFrame == self.selectedPhoneme.frame:
                        self.draggingEnd = 0
                else:
                    self.selectedPhrase = None
                    self.selectedWord = None
                    self.selectedPhoneme = None

            self.basicScrubbing = False
            if (self.selectedPhrase is None) and (self.selectedWord is None) and (self.selectedPhoneme is None):
                self.basicScrubbing = True
                self.oldFrame = 0
                self.doc.sound.PlaySegment(float(self.scrubFrame) / float(self.doc.fps), 15.0 / self.doc.fps, 1.0)
                self.mouthView.SetFrame(self.scrubFrame)
                self.UpdateDrawing(False)
            elif event.RightDown() and self.selectedWord:
                self.isDragging = False
                # manually enter the pronunciation for this word
                dlg = PronunciationDialog(self, self.doc.parent.phonemeset.set)
                dlg.wordLabel.SetLabel(dlg.wordLabel.GetLabel() + ' ' + self.selectedWord.text)
                phonemeString = ""
                for p in self.selectedWord.phonemes:
                    phonemeString += p.text + ' '
                dlg.phonemeCtrl.SetValue(phonemeString.strip())
                if dlg.ShowModal() == wx.ID_OK:
                    self.doc.dirty = True
                    self.selectedWord.phonemes = []
                    for p in dlg.phonemeCtrl.GetValue().split():
                        if len(p) == 0:
                            continue
                        phoneme = LipsyncPhoneme()
                        phoneme.text = p
                        self.selectedWord.phonemes.append(phoneme)
                    self.parentPhrase.RepositionWord(self.selectedWord)
                    self.UpdateDrawing()
                dlg.Destroy()
                self.isDragging = False
                self.draggingEnd = -1 # which end of the object (beginning or end) are you dragging
                self.selectedPhrase = None
                self.selectedWord = None
                self.selectedPhoneme = None
            elif event.LeftDClick():
                playSegment = False
                if self.selectedPhrase is not None:
                    playSegment = True
                    self.doc.sound.PlaySegment(float(self.selectedPhrase.startFrame) / float(self.doc.fps),
                            float(self.selectedPhrase.endFrame - self.selectedPhrase.startFrame + 1) / self.doc.fps,
                            1.0)
                elif self.selectedWord is not None:
                    playSegment = True
                    self.doc.sound.PlaySegment(float(self.selectedWord.startFrame) / float(self.doc.fps),
                            float(self.selectedWord.endFrame - self.selectedWord.startFrame + 1) / self.doc.fps,
                            1.0)
                elif self.selectedPhoneme is not None:
                    playSegment = True
                    self.doc.sound.PlaySegment(float(self.selectedPhoneme.frame) / float(self.doc.fps),
                            1.0 / self.doc.fps,
                            1.0)
                self.isDragging = False
                self.draggingEnd = -1 # which end of the object (beginning or end) are you dragging
                self.selectedPhrase = None
                self.selectedWord = None
                self.selectedPhoneme = None
                if playSegment:
                    frame = -1
                    while self.doc.sound.IsPlaying():
                        nextFrame = int(math.floor(self.doc.sound.CurrentTime() * self.doc.fps))
                        if frame != nextFrame:
                            frame = nextFrame
                            self.mouthView.SetFrame(frame)
                            #self.SetFrame(frame) # I'm not sure if it's good to display the playback marker during this operation or not
                            self.TheApp.Yield()
                        wx.MilliSleep(250.0 / self.doc.fps)
        if event.RightDown():
            self.isDragging = False
            self.draggingEnd = -1 # which end of the object (beginning or end) are you dragging
            self.selectedPhrase = None
            self.selectedWord = None
            self.selectedPhoneme = None
        if self.isDragging:
            self.CaptureMouse()

    def OnMouseUp(self, event):
        if self.isDragging:
            self.ReleaseMouse()
            self.isDragging = False
            self.scrubFrame = -1
            self.draggingEnd = -1
            self.selectedPhrase = None
            self.selectedWord = None
            self.selectedPhoneme = None
            if (self.doc is not None) and (self.doc.sound is not None):
                while self.doc.sound.IsPlaying():
                    pass # don't redraw until the playback for the last frame is done
            self.UpdateDrawing()

    def OnMouseWheel(self,event):
        if self.doc is not None:
            if event.ControlDown():
                if event.GetWheelRotation() > 0:
                    self.OnZoomIn(event)
                else:
                    self.OnZoomOut(event)

    def OnMouseMove(self, event):
        if self.isDragging:
            x, y = event.GetPositionTuple()
            x, y = self.CalcUnscrolledPosition(x, y)
            frame = x / self.frameWidth
            if frame == self.dragStartFrame:
                return
            self.dragStartFrame = -1000 # kick it far out of the way

            if self.selectedPhrase is not None:
                if self.draggingEnd == 0:
                    if frame != self.selectedPhrase.startFrame:
                        self.dragChange = True
                        self.doc.dirty = True
                        self.selectedPhrase.startFrame = frame
                        if self.selectedPhrase.startFrame > self.selectedPhrase.endFrame - 1:
                            self.selectedPhrase.startFrame = self.selectedPhrase.endFrame - 1
                        self.doc.currentVoice.RepositionPhrase(self.selectedPhrase, self.doc.soundDuration - 1)
                elif self.draggingEnd == 1:
                    if frame != self.selectedPhrase.endFrame:
                        self.dragChange = True
                        self.doc.dirty = True
                        self.selectedPhrase.endFrame = frame
                        if self.selectedPhrase.endFrame < self.selectedPhrase.startFrame + 1:
                            self.selectedPhrase.endFrame = self.selectedPhrase.startFrame + 1
                        self.doc.currentVoice.RepositionPhrase(self.selectedPhrase, self.doc.soundDuration - 1)
                elif self.draggingEnd == 2:
                    if frame != self.lastFrame:
                        self.dragChange = True
                        self.doc.dirty = True
                        self.selectedPhrase.startFrame += frame - self.lastFrame
                        self.selectedPhrase.endFrame += frame - self.lastFrame
                        self.doc.currentVoice.RepositionPhrase(self.selectedPhrase, self.doc.soundDuration - 1)
            elif self.selectedWord is not None:
                if self.draggingEnd == 0:
                    if frame != self.selectedWord.startFrame:
                        self.dragChange = True
                        self.doc.dirty = True
                        self.selectedWord.startFrame = frame
                        if self.selectedWord.startFrame > self.selectedWord.endFrame - 1:
                            self.selectedWord.startFrame = self.selectedWord.endFrame - 1
                        self.parentPhrase.RepositionWord(self.selectedWord)
                elif self.draggingEnd == 1:
                    if frame != self.selectedWord.endFrame:
                        self.dragChange = True
                        self.doc.dirty = True
                        self.selectedWord.endFrame = frame
                        if self.selectedWord.endFrame < self.selectedWord.startFrame:
                            self.selectedWord.endFrame = self.selectedWord.startFrame + 1
                        self.parentPhrase.RepositionWord(self.selectedWord)
                elif self.draggingEnd == 2:
                    if frame != self.lastFrame:
                        self.dragChange = True
                        self.doc.dirty = True
                        self.selectedWord.startFrame += frame - self.lastFrame
                        self.selectedWord.endFrame += frame - self.lastFrame
                        self.parentPhrase.RepositionWord(self.selectedWord)
            elif self.selectedPhoneme is not None:
                if self.draggingEnd == 0:
                    if frame != self.selectedPhoneme.frame:
                        self.dragChange = True
                        self.doc.dirty = True
                        self.selectedPhoneme.frame = frame
                        self.parentWord.RepositionPhoneme(self.selectedPhoneme)

            if (frame != self.scrubFrame) and (self.doc is not None) and (self.doc.sound is not None): # and (not self.doc.sound.IsPlaying()):
                self.oldFrame = self.scrubFrame
                self.scrubFrame = frame
                self.doc.sound.PlaySegment(float(self.scrubFrame) / float(self.doc.fps), 15.0 / self.doc.fps, 1.0)
                self.mouthView.SetFrame(self.scrubFrame)
                self.UpdateDrawing(not self.basicScrubbing)
                self.lastFrame = self.scrubFrame

    def SetFrame(self, frame):
        self.oldFrame = self.curFrame
        self.curFrame = frame
        # Scroll the window (if necessary) to make sure the current frame is visible
        cs = self.GetClientSize()
        curFrameX, curFrameY = self.CalcScrolledPosition(self.curFrame * self.frameWidth, 0)
        if curFrameX < 0 or curFrameX > cs.width:
            xs, ys = self.GetScrollPixelsPerUnit()
            self.Scroll(self.curFrame * self.frameWidth / xs, -1)
        self.UpdateDrawing(False)

    def SetDocument(self, doc):
        if (self.doc is None) and (doc is not None):
            self.sampleWidth = defaultSampleWidth
            self.samplesPerFrame = defaultSamplesPerFrame
            self.samplesPerSec = doc.fps * self.samplesPerFrame
            self.frameWidth = self.sampleWidth * self.samplesPerFrame
        self.doc = doc
        self.numSamples = 0
        self.amp = []
        self.maxWidth = 32
        self.maxHeight = 32
        if (self.doc is not None) and (self.doc.sound is not None):
            self.frameWidth = self.sampleWidth * self.samplesPerFrame
            duration = self.doc.sound.Duration()
            time = 0.0
            sampleDur = 1.0 / self.samplesPerSec
            maxAmp = 0.0
            while time < duration:
                self.numSamples = self.numSamples + 1
                amp = self.doc.sound.GetRMSAmplitude(time, sampleDur)
                self.amp.append(amp)
                if amp > maxAmp:
                    maxAmp = amp
                time = time + sampleDur
            # normalize amplitudes
            maxAmp = 0.95 / maxAmp
            for i in range(len(self.amp)):
                self.amp[i] = self.amp[i] * maxAmp
            self.maxWidth = (self.numSamples + 1) * self.sampleWidth
            self.maxHeight = self.GetClientSize().height
        elif self.doc is not None:
            self.maxWidth = self.doc.soundDuration * self.frameWidth
            self.maxHeight = self.GetClientSize().height
        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        # clear the current waveform
        dc = wx.ClientDC(self)
        self.PrepareDC(dc)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        if BUFFERED:
            # Initialize the buffer bitmap.  No real DC is needed at this point.
            if self.maxWidth > 0 and self.maxHeight > 0:
                self.buffer = wx.EmptyBitmap(self.maxWidth, self.maxHeight)
            else:
                self.buffer = None
            self.UpdateDrawing()

    def UpdateDrawing(self, redrawAll = True):
        if BUFFERED and self.buffer is None:
            print("Oh no!")
            return
        self.clipRect = None
        if (self.doc is not None) and (self.doc.sound is not None):
            cs = self.GetClientSize()
            if self.isDragging and self.basicScrubbing and (not redrawAll):
                firstSample = self.oldFrame * self.samplesPerFrame
                lastSample = self.scrubFrame * self.samplesPerFrame
                if firstSample > lastSample:
                    firstSample, lastSample = lastSample, firstSample
                firstSample -= self.samplesPerFrame * 2
                lastSample += self.samplesPerFrame * 3
                self.clipRect = wx.Rect((firstSample + 1) * self.sampleWidth, 0, (lastSample - firstSample - 2) * self.sampleWidth, cs.height)
            elif self.doc.sound.IsPlaying() and (not redrawAll):
                if self.curFrame >= self.oldFrame:
                    self.clipRect = wx.Rect(self.oldFrame * self.frameWidth, 0, (self.curFrame - self.oldFrame + 2) * self.frameWidth, cs.height)
        if BUFFERED:
            # If doing buffered drawing, create the buffered DC, giving it
            # it a real DC to blit to when done.
            cdc = wx.ClientDC(self)
            self.PrepareDC(cdc)
            #print(self.clipRect)
            if self.clipRect is not None:
                if not self.isWxPhoenix:
                    cdc.SetClippingRect(self.clipRect)
                else:
                    # WxWidgets - Phoenix
                    cdc.SetClippingRegion(self.clipRect)
            dc = wx.BufferedDC(cdc, self.buffer)
            if self.clipRect is not None:
                if not self.isWxPhoenix:
                    dc.SetClippingRect(self.clipRect)
                else:
                    # WxWidgets - Phoenix
                    dc.SetClippingRegion(self.clipRect)
            self.Draw(dc)
            self.Draw(cdc)
        else:
            dc = wx.ClientDC(self)
            self.PrepareDC(dc)
            if self.clipRect is not None:
                if not self.isWxPhoenix:
                    dc.SetClippingRect(self.clipRect)
                else:
                     # WxWidgets - Phoenix
                    dc.SetClippingRegion(self.clipRect)
            self.Draw(dc)

    def Draw(self, dc):
        if self.doc is None:
            #dc.BeginDrawing()
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()
            #dc.EndDrawing()
            return
        fillColor = wx.Colour(162, 205, 242)
        lineColor = wx.Colour(30, 121, 198)
        frameCol = wx.Colour(192, 192, 192)
        frameTextCol = wx.Colour(64, 64, 64)
        playBackCol = wx.Colour(255, 127, 127)
        playForeCol = wx.Colour(209, 102, 121)
        playOutlineCol = wx.Colour(128, 0, 0)
        textCol = wx.Colour(64, 64, 64)
        phraseFillCol = wx.Colour(205, 242, 162)
        phraseOutlineCol = wx.Colour(121, 198, 30)
        wordFillCol = wx.Colour(242, 205, 162)
        wordOutlineCol = wx.Colour(198, 121, 30)
        phonemeFillCol = wx.Colour(231, 185, 210)
        phonemeOutlineCol = wx.Colour(173, 114, 146)
        font = wx.Font(6, wx.SWISS, wx.NORMAL, wx.NORMAL)
        drawPlayMarker = False
        curFrame = self.curFrame
        cs = self.GetClientSize()
        halfClientHeight = cs.height / 2
        #dc.BeginDrawing()
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        firstSample = 0
        lastSample = len(self.amp)
        if (self.doc is not None) and (self.doc.sound is not None) and self.doc.sound.IsPlaying() and (not self.isDragging):
            if curFrame >= self.oldFrame:
                firstSample = (self.oldFrame - 1) * self.samplesPerFrame
                if firstSample < 0:
                    firstSample = 0
                lastSample = (curFrame + 2) * self.samplesPerFrame
                if lastSample > len(self.amp):
                    lastSample = len(self.amp)
            drawPlayMarker = True
            x = curFrame * self.frameWidth
            #print("OldFrame: ",self.oldFrame)
            #print("X for cursor :", x)
            # background of playback marker
            dc.SetBrush(wx.Brush(playBackCol))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle(x, 0, self.frameWidth + 1, cs.height)
        elif self.isDragging:
            scrollX, scrollY = self.CalcScrolledPosition(0, 0)
            firstSample = int(-scrollX / self.sampleWidth) - 1
            if self.basicScrubbing:
                firstSample = self.oldFrame * self.samplesPerFrame
            lastSample = firstSample + int(cs.width / self.sampleWidth) + 3
            if self.basicScrubbing:
                lastSample = self.scrubFrame * self.samplesPerFrame
                if firstSample > lastSample:
                    firstSample, lastSample = lastSample, firstSample
                firstSample -= self.samplesPerFrame * 2
                lastSample += self.samplesPerFrame * 3
            if firstSample < 0:
                firstSample = 0
            if firstSample > len(self.amp):
                firstSample = len(self.amp)
            if lastSample < 0:
                lastSample = 0
            if lastSample > len(self.amp):
                lastSample = len(self.amp)
            drawPlayMarker = True
            curFrame = self.scrubFrame
            x = curFrame * self.frameWidth
            # background of playback marker
            dc.SetBrush(wx.Brush(playBackCol))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle(x, 0, self.frameWidth + 1, cs.height)
        # draw the audio samples
        dc.SetBrush(wx.Brush(fillColor))
        dc.SetPen(wx.Pen(lineColor))
        dc.SetTextForeground(frameTextCol)
        dc.SetFont(font)
        textWidth, topBorder = dc.GetTextExtent("Ojyg")
        x = firstSample * self.sampleWidth
        frame = firstSample / self.samplesPerFrame
        fps = int(round(self.doc.fps))
        sample = firstSample
        lastHeight = -1
        lastHalfHeight = 1
        amp = 0
        for i in range(int(firstSample), int(lastSample)):
            if (sample + 1) % self.samplesPerFrame == 0:
                # draw frame marker
                dc.SetPen(wx.Pen(frameCol))
                frameX = (frame + 1) * self.frameWidth
                #print("framex: ",frameX)
                if (self.frameWidth > 2) or ((frame + 2) % fps == 0):
                    dc.DrawLine(frameX, topBorder, frameX, cs.height)
                # draw frame label
                if (self.frameWidth > 30) or ((frame + 2) % 5 == 0):
                    dc.DrawLine(frameX, 0, frameX, topBorder)
                    dc.DrawLine(frameX+1,0,frameX+1, cs.height)
                    dc.DrawLabel(str(frame + 2), wx.Rect(frameX + 1, 0, 128, 128))
                dc.SetBrush(wx.Brush(fillColor))
                dc.SetPen(wx.Pen(lineColor))
            amp = self.amp[i]
            height = round(cs.height * amp)
            halfHeight = height / 2
            if drawPlayMarker and (frame == curFrame):
                dc.SetBrush(wx.Brush(playForeCol))
                dc.SetPen(wx.TRANSPARENT_PEN)
            if SIMPLE_DISPLAY:
                dc.DrawLine(x, halfClientHeight - halfHeight, x, halfClientHeight + halfHeight)
            else:
                dc.DrawRectangle(x, halfClientHeight - halfHeight, self.sampleWidth + 1, height)
                if drawPlayMarker and (frame == curFrame):
                    dc.SetBrush(wx.Brush(fillColor))
                    dc.SetPen(wx.Pen(lineColor))
                if lastHeight > 0 and not (drawPlayMarker and frame == curFrame):
                    if lastHeight > height:
                        lastHeight = height
                        lastHalfHeight = halfHeight
                    dc.SetPen(wx.Pen(fillColor))
                    dc.DrawLine(x, halfClientHeight - lastHalfHeight + 1, x, halfClientHeight + lastHalfHeight - 1)
                    dc.SetPen(wx.Pen(lineColor))
            x = x + self.sampleWidth
            sample = sample + 1
            if sample % self.samplesPerFrame == 0:
                frame = frame + 1
                """
                # draw frame markers
                frameX = frame * self.frameWidth
                dc.SetPen(wx.Pen(frameCol))
                dc.DrawLine(frameX, topBorder, frameX, cs.height)
                dc.SetBrush(wx.Brush(fillColor))
                dc.SetPen(wx.Pen(lineColor))
                """
            lastHeight = height
            lastHalfHeight = halfHeight
        # draw the phrases/words/phonemes
        if self.doc.currentVoice is not None:
            topBorder = topBorder + 4
            font.SetPointSize(8)
            font.SetWeight(wx.BOLD)
            dc.SetFont(font)
            textWidth, textHeight = dc.GetTextExtent("Ojyg")
            textHeight = textHeight + 6
            self.phraseBottom = topBorder + textHeight
            self.wordBottom = topBorder + 4 + textHeight + textHeight + textHeight
            self.phonemeTop = cs.height - 4 - textHeight - textHeight
            dc.SetTextForeground(textCol)
            for phrase in self.doc.currentVoice.phrases:
                dc.SetBrush(wx.Brush(phraseFillCol))
                dc.SetPen(wx.Pen(phraseOutlineCol))
                r = wx.Rect(phrase.startFrame * self.frameWidth, topBorder, (phrase.endFrame - phrase.startFrame + 1) * self.frameWidth + 1, textHeight)
                if (self.clipRect is not None) and (not r.Intersects(self.clipRect)):
                    continue # speed things up by skipping off-screen phrases
                phrase.top = r.y
                phrase.bottom = r.y + r.height
                dc.DrawRectangle(r.x, r.y, r.width, r.height)
                r.Inflate(-4, 0)
                if not self.isWxPhoenix:
                    dc.SetClippingRect(r)
                else:
                     # WxWidgets - Phoenix
                    dc.SetClippingRegion(r)
                dc.DrawLabel(phrase.text, r, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
                dc.DestroyClippingRegion()
                if self.clipRect is not None:
                    if not self.isWxPhoenix:
                        dc.SetClippingRect(self.clipRect)
                    else:
                        # WxWidgets - Phoenix
                        dc.SetClippingRegion(self.clipRect)

                wordCount = 0
                for word in phrase.words:
                    dc.SetBrush(wx.Brush(wordFillCol))
                    dc.SetPen(wx.Pen(wordOutlineCol))
                    r = wx.Rect(word.startFrame * self.frameWidth, topBorder + 4 + textHeight, (word.endFrame - word.startFrame + 1) * self.frameWidth + 1, textHeight)
                    if wordCount % 2:
                        r.y = r.y + textHeight
                    word.top = r.y
                    word.bottom = r.y + r.height
                    dc.DrawRectangle(r.x, r.y, r.width, r.height)
                    r.Inflate(-4, 0)
                    if not self.isWxPhoenix:
                        dc.SetClippingRect(r)
                    else:
                         # WxWidgets - Phoenix
                        dc.SetClippingRegion(r)
                    dc.DrawLabel(word.text, r, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
                    dc.DestroyClippingRegion()
                    if self.clipRect is not None:
                        if not self.isWxPhoenix:
                            dc.SetClippingRect(self.clipRect)
                        else:
                             # WxWidgets - Phoenix
                            dc.SetClippingRegion(self.clipRect)
                    dc.SetBrush(wx.Brush(phonemeFillCol))
                    dc.SetPen(wx.Pen(phonemeOutlineCol))
                    phonemeCount = 0
                    for phoneme in word.phonemes:
                        r = wx.Rect(phoneme.frame * self.frameWidth, cs.height - 4 - textHeight, self.frameWidth + 1, textHeight)
                        if phonemeCount % 2:
                            r.y = r.y - textHeight
                        phoneme.top = r.y
                        phoneme.bottom = r.y + r.height
                        dc.DrawRectangle(r.x, r.y, r.width, r.height)
                        dc.DrawLabel(phoneme.text, r, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
                        phonemeCount = phonemeCount + 1
                    wordCount = wordCount + 1
        # draw the play marker
        if drawPlayMarker:
            x = curFrame * self.frameWidth
            # foreground
            height = round(cs.height * amp)
            # outline
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.SetPen(wx.Pen(playOutlineCol))
            dc.DrawRectangle(x, 0, self.frameWidth + 1, cs.height)
            # Draw Big Fat Frame Marker
            if self.isDragging:
                  dc.DestroyClippingRegion()
                  font.SetPointSize(16)
                  font.SetWeight(wx.BOLD)
                  dc.SetFont(font)
                  dc.DrawLabel(str(curFrame + 1), wx.Rect(x-50, cs.height*0.4, 100,125),wx.ALIGN_CENTER)


        dc.EndDrawing()

    def OnZoomIn(self, event):
        if (self.doc is not None) and (self.samplesPerFrame < 16):
            self.samplesPerFrame = self.samplesPerFrame * 2
            self.samplesPerSec = self.doc.fps * self.samplesPerFrame
            self.frameWidth = self.sampleWidth * self.samplesPerFrame
            self.SetDocument(self.doc)

    def OnZoomOut(self, event):
        if (self.doc is not None) and (self.samplesPerFrame > 1):
            self.samplesPerFrame = self.samplesPerFrame / 2
            self.samplesPerSec = self.doc.fps * self.samplesPerFrame
            self.frameWidth = self.sampleWidth * self.samplesPerFrame
            self.SetDocument(self.doc)

    def OnZoom1(self, event):
        if self.doc is not None:
            self.sampleWidth = defaultSampleWidth
            self.samplesPerFrame = defaultSamplesPerFrame
            self.samplesPerSec = self.doc.fps * self.samplesPerFrame
            self.frameWidth = self.sampleWidth * self.samplesPerFrame
            self.SetDocument(self.doc)

# end of class WaveformView


