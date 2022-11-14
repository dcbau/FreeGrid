from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
from scipy.signal import resample

matplotlib.rcParams.update({'axes.titlesize': 8})
matplotlib.rcParams.update({'axes.labelsize': 7})
matplotlib.rcParams.update({'xtick.labelsize': 7})
matplotlib.rcParams.update({'ytick.labelsize': 7})
matplotlib.rcParams.update({'axes.titleweight': 'bold'})

class SignalPlotWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(SignalPlotWidget, self).__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.plot_tab_widget = QtWidgets.QTabWidget()
        self.plot_tab_widget.setEnabled(True)
        self.plot_tab_widget.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.plot_tab_widget.setTabPosition(QtWidgets.QTabWidget.South)
        self.plot_tab_widget.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.plot_tab_widget.setIconSize(QtCore.QSize(32, 32))
        self.plot_tab_widget.setDocumentMode(True)
        self.plot_tab_widget.setTabsClosable(False)
        self.plot_tab_widget.setMovable(False)
        self.plot_tab_widget.setTabBarAutoHide(False)
        self.plot_tab_widget.setObjectName("plot_tab_widget")

        self.tab_rec = QtWidgets.QWidget()
        self.tab_rec.setEnabled(True)
        self.tab_rec.setObjectName("tab_rec")
        self.tab_rec.setLayout(QtWidgets.QVBoxLayout())
        self.plot_tab_widget.addTab(self.tab_rec, "")

        self.tab_ir = QtWidgets.QWidget()
        self.tab_ir.setEnabled(True)
        self.tab_ir.setObjectName("tab_ir")
        self.tab_ir.setLayout(QtWidgets.QVBoxLayout())
        self.plot_tab_widget.addTab(self.tab_ir, "")

        self.plot1 = Figure()
        self.plot1.set_facecolor("none")
        self.plot1_canvas = FigureCanvas(self.plot1)
        self.plot1_canvas.setStyleSheet("background-color:transparent;")
        self.tab_rec.layout().addWidget(self.plot1_canvas)

        self.plot2 = Figure()
        self.plot2.set_facecolor("none")
        self.plot2_canvas = FigureCanvas(self.plot2)
        self.plot2_canvas.setStyleSheet("background-color:transparent;")
        self.tab_ir.layout().addWidget(self.plot2_canvas)

        self.layout().addWidget(self.plot_tab_widget)

        self.plot_tab_widget.setTabText(0, "REC")
        self.plot_tab_widget.setTabText(1, "IR")

        self.spec_nfft = 512

        self.spec_noverlap = 300

        #self.plot_color = '#606060'
        self.plot_color = 'xkcd:teal'
        self.plot_linewidth = 1


    def plot_recordings(self, rec_l, rec_r, fb_loop, fs=None, plot='waveform', fb_loop_used=False):

        self.plot1.clf()
        self.plot1.subplots_adjust(hspace=0.4)

        t = np.arange(0, np.size(rec_l)) / fs

        ax1 = self.plot1.add_subplot(311)
        ax1.clear()
        if plot == 'waveform':
            ax1.plot(t, rec_l, color=self.plot_color, linewidth=self.plot_linewidth)
            ax1.set_ylim([-1, 1])
            ax1.set_yticks([-1, -0.5, 0, 0.5, 1])
            ax1.set_ylabel('Amplitude')
            ax1.grid(linestyle='--', alpha=0.5, linewidth=0.5)
            #ax1.set_xlim([0, t[-1]])
        elif plot == 'spectrogram':
            _,_,_, cax  = ax1.specgram(rec_l, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
            self.plot1.colorbar(cax)
            ax1.set_ylabel('Frequency in Hz')

        ax1.set_title("Recorded Signal Ch1 (Left)", loc='left')

        if rec_r is not None:
            ax2 = self.plot1.add_subplot(312)
            ax2.clear()
            if plot == 'waveform':
                ax2.plot(t, rec_r, color=self.plot_color, linewidth=self.plot_linewidth)
                ax2.set_ylim([-1, 1])
                ax2.set_yticks([-1, -0.5, 0, 0.5, 1])
                ax2.set_ylabel('Amplitude')
                ax2.grid(linestyle='--', alpha=0.5, linewidth=0.5)
                #ax2.set_xlim([0, t[-1]])

            elif plot == 'spectrogram':
                _,_,_, cax2  = ax2.specgram(rec_r, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
                self.plot1.colorbar(cax2)
                ax2.set_ylabel('Frequency in Hz')

            ax2.set_title("Recorded Signal Ch2 (Right)", loc='left')

        ax3 = self.plot1.add_subplot(313)
        ax3.clear()
        if plot == 'waveform':
            ax3.plot(t, fb_loop, color=self.plot_color, linewidth=self.plot_linewidth)
            ax3.set_ylim([-1, 1])
            ax3.set_yticks([-1, -0.5, 0, 0.5, 1])
            ax3.set_ylabel('Amplitude')
            ax3.grid(linestyle='--', alpha=0.5, linewidth=0.5)
            #ax3.set_xlim([0, t[-1]])

        elif plot == 'spectrogram':
            _,_,_, cax3  = ax3.specgram(fb_loop, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
            self.plot1.colorbar(cax3)
            ax3.set_ylabel('Frequency in Hz')

        ax3.set_xlabel('Time in s')

        if fb_loop_used:
            ax3.set_title("Recorded Signal Ch3 (Feedback Loop)", loc='left')
        else:
            ax3.set_title("Excitation Signal (No Feedback Loop)", loc='left')


        self.plot1_canvas.draw()


    def plot_IRs(self, ir_l, ir_r, fs=None, plot='waveform_log'):

        self.plot2.clf()
        #self.plot2.subplots_adjust(hspace=0.4)

        ax1 = self.plot2.add_subplot(211)
        ax1.clear()



        if plot=='waveform_log':
            t = np.arange(0, np.size(ir_l)) / fs
            logwaveform = 20*np.log10(np.abs(ir_l))
            ax1.plot(t, logwaveform, color=self.plot_color, linewidth=self.plot_linewidth)
            ax1.set_ylim([-120, np.max([np.max(logwaveform), 12])])
            ax1.set_ylabel("Magnitude in dB")
            ax1.set_yticks([-120, -90, -60, -36, -24, -12, 0, np.max([np.max(logwaveform), 12])])
            ax1.grid(linestyle='--', alpha=0.5, linewidth=0.5)
            #ax1.set_xlim([0, t[-1]])

            #ax1.set_xlabel('Time in s')

        elif plot=='waveform':
            t = np.arange(0, np.size(ir_l)) / fs
            ax1.plot(t, ir_l, color=self.plot_color, linewidth=self.plot_linewidth)
            ax1.set_ylabel('Amplitude')
            #ax1.set_xlim([0, t[-1]])


            #ax1.set_xlabel('Time in s')

            ax1.set_ylim([-1, 1])
        elif plot=='spectrogram':
            _,_,_, cax = ax1.specgram(ir_l, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
            self.plot2.colorbar(cax).set_label('dB')
            #ax1.set_ylabel('Frequency in Hz')

        ax1.set_title("Impulse Response Ch1 (Left)", loc='left')


        if ir_r is not None:
            ax2 = self.plot2.add_subplot(212, sharex=ax1)
            ax2.clear()

            if plot=='waveform_log':
                t = np.arange(0, np.size(ir_r)) / fs
                logwaveform = 20 * np.log10(np.abs(ir_r))
                ax2.plot(t, logwaveform, color=self.plot_color, linewidth=self.plot_linewidth)
                ax2.set_ylim([-120, np.max([np.max(logwaveform), 12])])
                ax2.set_yticks([-120, -90, -60, -36, -24, -12, 0, np.max([np.max(logwaveform), 12])])
                ax2.set_ylabel("Magnitude in dB")
                ax2.grid(linestyle='--', alpha=0.5, linewidth=0.5)
                #ax2.set_xlim([0, t[-1]])


            elif plot == 'waveform':
                t = np.arange(0, np.size(ir_r)) / fs
                ax2.plot(t, ir_r, color=self.plot_color, linewidth=self.plot_linewidth)
                ax2.set_ylabel('Amplitude')
                #ax2.set_xlim([0, t[-1]])

            elif plot=='spectrogram':
                _,_,_, cax2 = ax2.specgram(ir_r, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
                self.plot2.colorbar(cax2).set_label('dB')
                ax2.set_ylabel('Frequency in Hz')

            ax2.set_xlabel('Time in s')
            ax2.set_title("Impulse Response Ch2 (Right)", loc='left')


        self.plot2_canvas.draw()

class PlotWidget_HPIRs(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(PlotWidget_HPIRs, self).__init__(*args, **kwargs)


        self.plot_hpirs = Figure()
        self.plot_hpirs.set_facecolor("none")
        self.plot_hpirs_canvas = FigureCanvas(self.plot_hpirs)
        self.plot_hpirs_canvas.setStyleSheet("background-color:transparent;")

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.plot_hpirs_canvas)


    def plot_hptf(self, hpc_irs, hpc_average=None, fs=None):

        try:
            M = np.size(hpc_irs, 0)
            N = np.size(hpc_irs, 2)
        except IndexError:
            M = 0
            N = 0

        plot_resolution = 1025
        nyquist = int(N / 2 + 1)

        f_vals = np.linspace(0, fs/2, plot_resolution)


        self.plot_hpirs.clf()

        self.plot_hpirs.subplots_adjust(hspace=0.5)

        ax1 = self.plot_hpirs.add_subplot(211)
        ax1.clear()
        ax1.set_title("Headphone IR L (normalized)", loc='left')
        ax1.set_ylabel('Magnitude in dB')
        ax1.grid(linestyle='--', alpha=0.5, linewidth=0.5, which='both')


        ax2 = self.plot_hpirs.add_subplot(212, sharey=ax1, sharex=ax1)
        ax2.clear()
        ax2.set_title("Headphone IR R (normalized)", loc='left')
        ax2.set_xscale('log')
        ax2.set_xlim(10, fs/2)
        ax2.set_xticks([20, 100, 1000, 10000, 20000])
        ax2.set_xticklabels(['20', '100', '1k', '10k', '20k'])
        ax2.set_ylabel('Magnitude in dB')
        ax2.grid(linestyle='--', alpha=0.5, linewidth=0.5, which='both')

        ax2.set_xlabel('Frequency in Hz')

        if M != 0:
            _hpc_irs = np.copy(hpc_irs)

            #normalize
            _hpc_irs = _hpc_irs / np.amax(_hpc_irs)

            magFilter = np.fft.fft(_hpc_irs, axis=2)
            magFilter = 20 * np.log10(np.abs(magFilter[:, :, :nyquist]))
            magFilter = resample(magFilter, plot_resolution, axis=2)

            for i in range(M):
                ax1.plot(f_vals, magFilter[i, 0, :], linewidth=0.5)
                ax2.plot(f_vals, magFilter[i, 1, :], linewidth=0.5)

            max_val = np.max(magFilter)
        else:
            max_val=0

        ax2.set_ylim([-50, max(max_val + 1, 12)])
        ax2.set_yticks([-48, -36, -24, -12, 0, 12])

        self.plot_hpirs_canvas.draw()

class PlotWidget_HPCF(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(PlotWidget_HPCF, self).__init__(*args, **kwargs)

        self.plot_hpc = Figure()
        self.plot_hpc.set_facecolor('none')
        self.plot_hpc_canvas = FigureCanvas(self.plot_hpc)
        self.plot_hpc_canvas.setStyleSheet("background-color:transparent;")


        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.plot_hpc_canvas)




        #self.plot_color = '#606060'
        self.plot_color_1 = 'xkcd:teal'
        self.plot_color_2 = 'xkcd:tomato'

        self.plot_linewidth = 2


    def plot_hpcf(self, H_l, H_r, fs=None):

        #matplotlib.rcParams.update({'font.size': 5})

        ax = self.plot_hpc.gca()

        ax.clear()
        ax.set_title("Headphone Compensation (Estimate)", loc='left')
        ax.set_xscale('log')
        ax.set_xlim(10, fs/2)
        #ax.set_ylim(-30, 10)
        ax.set_xticks([20, 100, 1000, 10000, 20000])
        ax.set_xticklabels(['20', '100', '1k', '10k', '20k'])
        ax.set_ylabel('Magnitude in dB')

        ax.set_xlabel('Frequency in Hz')
        ax.grid(linestyle='--', alpha=0.5, linewidth=0.5, which='both')

        nq = int(np.size(H_l) / 2 + 1)
        f_vals = np.linspace(0, 24000, nq)

        try:
            magFilter_l = H_l
            magFilter_l = magFilter_l[:nq]
            magFilter_l = 20 * np.log10(abs(magFilter_l))
            l, = ax.plot(f_vals, magFilter_l, linewidth=self.plot_linewidth, color=self.plot_color_1)
            l.set_label("Left Ear")

            magFilter_r = H_r
            magFilter_r = magFilter_r[:nq]
            magFilter_r = 20 * np.log10(abs(magFilter_r))
            r, = ax.plot(f_vals, magFilter_r, linewidth=self.plot_linewidth, color=self.plot_color_2)
            r.set_label("Right Ear")


            ax.legend()

            max_val = max(np.max(magFilter_l), np.max(magFilter_r))



        except ValueError:
            max_val=0

        ax.set_ylim([-50, max(max_val + 1, 12)])
        ax.set_yticks([-48, -36, -24, -12, 0, 12])


        # # set y limits according to displayed values
        # low, high = ax.get_xlim()
        # plotted_bin_ids = np.where((f_vals > low) & (f_vals < high))
        #
        # low_y = np.array([magFilter_l[plotted_bin_ids], magFilter_l[plotted_bin_ids]]).min()
        # high_y = np.array([magFilter_r[plotted_bin_ids], magFilter_r[plotted_bin_ids]]).max()
        #
        # ax.set_ylim((low_y+5) + (5-np.mod((a+5), 5)), high_y)

        self.plot_hpc_canvas.draw()
