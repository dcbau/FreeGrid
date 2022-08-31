import numpy as np
from scipy.signal import windows, firwin, firwin2, chirp, unit_impulse, butter, sosfilt
from numpy.fft import fft, ifft, rfft, irfft

def make_HPCF(hp_IRs, beta_regularization, fs):
    # algorithm taken in modified form from
    # https://github.com/spatialaudio/hptf-compensation-filters/blob/master/Calc_HpTF_compensation_filter.m
    # Copyright (c) 2016 Vera Erbes
    # licensed under MIT license


    # parameters
    ####################
    filter_length = 4096
    window_length = 1024

    #regularization parameters
    fc_highshelf = 6000
    beta = beta_regularization

    M = np.size(hp_IRs, 0)

    # algorithm
    #######################
    # create normalized working copies
    hl_raw = hp_IRs[:, 0, :] / hp_IRs.max()
    hr_raw = hp_IRs[:, 1, :] / hp_IRs.max()

    # approximate onsets and shift IRs to compensate delay
    onsets_l = np.argmax(hl_raw, axis=1)
    onsets_r = np.argmax(hr_raw, axis=1)

    for m in range(M):
        hl_raw[m, :] = np.roll(hl_raw[m, :], -(onsets_l[m]-50))
        hr_raw[m, :] = np.roll(hr_raw[m, :], -(onsets_r[m]-50))


    # window IRs and truncate
    win = windows.blackmanharris(window_length)
    win[:int(window_length/2)] = 1
    win = np.pad(win, (0, filter_length-window_length))

    hl_win = hl_raw[:, : filter_length] * win
    hr_win = hr_raw[:, : filter_length] * win

    # complex mean of HpTFs
    Hl = fft(hl_win, axis=1)
    Hr = fft(hr_win, axis=1)

    Hl_mean = np.mean(Hl, axis=0)
    Hr_mean = np.mean(Hr, axis=0)

    # bandpass
    f_low = 20 / (fs/2)
    f_high = 18000 / (fs/2)
    stopatt = 60
    beta_kaiser = .1102*(stopatt-8.7)

    b = firwin(filter_length,
                            [f_low, f_high],
                            pass_zero='bandpass',
                            window=('kaiser', beta_kaiser))
    BP = fft(b)

    # regularization filter
    freq = np.array([0, 2000 / (fs/2), fc_highshelf / (fs/2), 1])
    G = np.array([-20, -20, 0, 0])
    g = 10**(G/20)
    b = firwin2(51, freq, g)
    b = np.pad(b, (0, filter_length-np.size(b)))
    RF = fft(b)

    # calculate complex filter
    Hcl = BP * np.conj(Hl_mean) / (Hl_mean * np.conj(Hl_mean) + beta * RF * np.conj(RF))
    Hcr = BP * np.conj(Hr_mean) / (Hr_mean * np.conj(Hr_mean) + beta * RF * np.conj(RF))

    return Hcl, Hcr

def deconvolve_stereo(x, y1, y2, fs, max_inv_dyn=None, lowpass=None, highpass=None):
    ir1 = deconvolve(x, y1, fs, max_inv_dyn, lowpass, highpass)
    ir2 = deconvolve(x, y2, fs, max_inv_dyn, lowpass, highpass)
    return ir1, ir2

# deconvolution method similar to AKdeconv() from the AKtools matlab toolbox
def deconvolve(x, y, fs, max_inv_dyn=None, lowpass=None, highpass=None):
    input_length = np.size(x)
    n = np.ceil(np.log2(input_length)) + 1
    N_fft = int(pow(2, n))

    # transform
    X_f = rfft(x, N_fft)
    Y_f = rfft(y, N_fft)

    # invert input signal
    X_inv = 1 / X_f

    if max_inv_dyn is not None:
        # identify bins that exceed max inversion dynamic
        min_mag = np.min(np.abs(X_inv))
        mag_limit = min_mag * pow(10, np.abs(max_inv_dyn) / 20)
        ids_exceed = np.where(abs(X_inv) > mag_limit)

        # clip magnitude and leave phase untouched
        X_inv[ids_exceed] = mag_limit * np.exp(1j * np.angle(X_inv[ids_exceed]))

    if lowpass is not None or highpass is not None:
        # make fir filter by pushing a dirac through a butterworth SOS (multiple times)
        lp_filter = hp_filter = unit_impulse(N_fft)

        # lowpass
        if lowpass is not None:
            sos_lp = butter(lowpass[1], lowpass[0], 'lowpass', fs=fs, output='sos')
            for i in range(lowpass[2]):
                lp_filter = sosfilt(sos_lp, lp_filter)
        lp_filter = rfft(lp_filter)

        # highpass
        if highpass is not None:
            sos_hp = butter(highpass[1], highpass[0], 'highpass', fs=fs, output='sos')
            for i in range(highpass[2]):
                hp_filter = sosfilt(sos_hp, hp_filter)
        hp_filter = rfft(hp_filter)

        lp_hp_filter = hp_filter * lp_filter

        # apply filter
        X_inv = X_inv * lp_hp_filter

    # deconvolve
    H = Y_f * X_inv

    # backward transform
    h = irfft(H, N_fft)

    # truncate to original length
    h = h[:input_length]

    return h

def make_excitation_sweep(fs, num_channels=1, d_sweep_sec=3, d_post_silence_sec=1, f_start=20, f_end=20000, amp_db=-20, fade_out_samples=100):

    amplitude_lin = 10 ** (amp_db / 20)

    # make sweep
    t_sweep = np.linspace(0, d_sweep_sec, int(d_sweep_sec * fs))
    sweep = amplitude_lin * chirp(t_sweep, f0=f_start, t1=d_sweep_sec, f1=f_end, method='logarithmic', phi=90)

    # squared cosine fade
    fade_tmp = np.cos(np.linspace(0, np.pi / 2, fade_out_samples)) ** 2
    window = np.ones(np.size(sweep, 0))
    window[np.size(window) - fade_out_samples: np.size(window)] = fade_tmp
    sweep = sweep * window

    pre_silence = int(fs * 0.01) # 10msec post silence for safety while playback
    post_silence = int(fs * d_post_silence_sec)


    excitation = np.pad(sweep, (pre_silence, post_silence))

    excitation = np.tile(excitation, (num_channels, 1))  # make stereo or more, for out channels 1 & 2
    excitation = np.transpose(excitation).astype(np.float32)

    return excitation