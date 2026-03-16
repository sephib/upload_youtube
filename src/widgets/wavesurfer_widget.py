"""Wavesurfer AnyWidget for marimo - Interactive Audio Waveform Visualization.

Edited by Claude Code

This widget wraps wavesurfer.js v7 to provide interactive audio waveform display
with region support for audio segment annotation and editing.

Usage:
    import marimo as mo
    from src.widgets.wavesurfer_widget import WavesurferWidget

    with open("audio.mp3", "rb") as f:
        audio_bytes = f.read()

    widget = WavesurferWidget(
        audio_data=audio_bytes,
        regions=[
            {"id": "v1", "start": 0.0, "end": 5.3, "label": "Verse 1",
             "color": "rgba(100, 149, 237, 0.3)"},
        ],
    )

    widget_ui = mo.ui.anywidget(widget)
"""

import anywidget
import traitlets


class WavesurferWidget(anywidget.AnyWidget):
    """Interactive audio waveform widget using wavesurfer.js.

    Attributes:
        audio_data: Audio file as bytes (converted to blob URL in JS)
        regions: List of region dicts {id, start, end, label, color, drag, resize}
        current_time: Current playback position in seconds
        is_playing: Whether audio is currently playing
        selected_region_id: ID of currently selected region
        duration: Total audio duration in seconds (set by JS)
        waveform_color: Color of the waveform
        progress_color: Color of the played portion
        height: Height of waveform in pixels
        zoom_level: Pixels per second (horizontal zoom)
        play_range: [start, end] for isolated segment playback
    """

    # Audio data (Python -> JavaScript)
    audio_data = traitlets.Bytes(default_value=b"").tag(sync=True)

    # Regions (bidirectional)
    regions = traitlets.List(trait=traitlets.Dict()).tag(sync=True)

    # Playback state (bidirectional)
    current_time = traitlets.Float(default_value=0.0).tag(sync=True)
    is_playing = traitlets.Bool(default_value=False).tag(sync=True)

    # Selection state (bidirectional)
    selected_region_id = traitlets.Unicode(default_value="").tag(sync=True)

    # Audio metadata (JavaScript -> Python)
    duration = traitlets.Float(default_value=0.0).tag(sync=True)

    # Appearance (Python -> JavaScript)
    waveform_color = traitlets.Unicode(default_value="#4F4A85").tag(sync=True)
    progress_color = traitlets.Unicode(default_value="#383351").tag(sync=True)
    height = traitlets.Int(default_value=128).tag(sync=True)

    # Zoom (Python <-> JavaScript)
    zoom_level = traitlets.Int(default_value=50).tag(sync=True)

    # Isolated segment playback (Python -> JavaScript)
    play_range = traitlets.List(
        trait=traitlets.Float(), default_value=[]
    ).tag(sync=True)

    _esm = """
    import WaveSurfer from 'https://cdn.jsdelivr.net/npm/wavesurfer.js@7/dist/wavesurfer.esm.js';
    import RegionsPlugin from 'https://cdn.jsdelivr.net/npm/wavesurfer.js@7/dist/plugins/regions.esm.js';
    import TimelinePlugin from 'https://cdn.jsdelivr.net/npm/wavesurfer.js@7/dist/plugins/timeline.esm.js';

    // Confidence-based region colors
    const REGION_COLORS = {
      normal:      'rgba(100, 149, 237, 0.3)',  // cornflower blue (confidence >= 0.85)
      lowConf:     'rgba(255, 165, 0, 0.4)',    // orange (confidence < 0.85)
      selected:    'rgba(255, 215, 0, 0.5)',    // gold
      corrected:   'rgba(50, 205, 50, 0.3)',    // green
    };

    function regionColor(region) {
      if (region.corrected) return REGION_COLORS.corrected;
      if (region.confidence !== undefined && region.confidence < 0.85) return REGION_COLORS.lowConf;
      return region.color || REGION_COLORS.normal;
    }

    function fmtTime(s) {
      const m = Math.floor(s / 60);
      const sec = (s % 60).toFixed(3);
      return `${m}:${sec.padStart(6, '0')}`;
    }

    function render({ model, el }) {
      // ── Container structure ──
      const container = document.createElement('div');
      container.style.width = '100%';
      container.style.fontFamily = 'system-ui, sans-serif';

      const waveformDiv = document.createElement('div');
      waveformDiv.id = 'wf-' + Math.random().toString(36).slice(2, 9);

      // ── Controls bar ──
      const controls = document.createElement('div');
      controls.style.cssText = 'margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;';

      const btn = (label) => {
        const b = document.createElement('button');
        b.textContent = label;
        b.style.cssText = 'padding:6px 14px;cursor:pointer;font-size:13px;border:1px solid #ccc;border-radius:4px;background:#fff;';
        return b;
      };

      const playPauseBtn = btn('Play');
      const zoomInBtn = btn('Zoom +');
      const zoomOutBtn = btn('Zoom -');

      const timeDisplay = document.createElement('span');
      timeDisplay.style.cssText = 'font-family:monospace;font-size:13px;margin-left:auto;';
      timeDisplay.textContent = '0:00.000 / 0:00.000';

      const regionInfo = document.createElement('div');
      regionInfo.style.cssText = 'margin-top:8px;padding:8px;background:#f5f5f5;border-radius:4px;font-size:13px;min-height:20px;';
      regionInfo.textContent = 'Click a region to select it';

      controls.append(playPauseBtn, zoomInBtn, zoomOutBtn, timeDisplay);
      container.append(waveformDiv, controls, regionInfo);
      el.appendChild(container);

      // ── Plugins ──
      const regionsPlugin = RegionsPlugin.create();
      const timelinePlugin = TimelinePlugin.create({
        height: 20,
        timeInterval: 0.5,
        primaryLabelInterval: 5,
        style: { fontSize: '10px', color: '#6B7280' },
      });

      // ── WaveSurfer instance ──
      const ws = WaveSurfer.create({
        container: waveformDiv,
        waveColor: model.get('waveform_color'),
        progressColor: model.get('progress_color'),
        height: model.get('height'),
        minPxPerSec: model.get('zoom_level'),
        normalize: true,
        plugins: [regionsPlugin, timelinePlugin],
      });

      // Track state to avoid feedback loops
      let _suppressRegionSync = false;
      let _playRangeEnd = null;

      // ── Load audio ──
      const loadAudio = () => {
        const data = model.get('audio_data');
        if (data && data.byteLength > 0) {
          const blob = new Blob([data], { type: 'audio/mpeg' });
          const url = URL.createObjectURL(blob);
          ws.load(url);
        }
      };
      loadAudio();

      // ── Helpers ──
      const addRegionsFromModel = () => {
        regionsPlugin.clearRegions();
        const regions = model.get('regions') || [];
        const selectedId = model.get('selected_region_id');
        regions.forEach((r) => {
          const color = (r.id === selectedId) ? REGION_COLORS.selected : regionColor(r);
          regionsPlugin.addRegion({
            id: r.id,
            start: r.start,
            end: r.end,
            color: color,
            drag: r.drag !== false,
            resize: r.resize !== false,
            content: r.label || '',
          });
        });
      };

      const highlightSelected = (selectedId) => {
        const regions = model.get('regions') || [];
        regionsPlugin.getRegions().forEach((wsRegion) => {
          const modelRegion = regions.find((r) => r.id === wsRegion.id);
          if (wsRegion.id === selectedId) {
            wsRegion.setOptions({ color: REGION_COLORS.selected });
          } else if (modelRegion) {
            wsRegion.setOptions({ color: regionColor(modelRegion) });
          }
        });
      };

      // ── WaveSurfer events ──
      ws.on('ready', () => {
        const dur = ws.getDuration();
        model.set('duration', dur);
        model.save_changes();
        timeDisplay.textContent = `0:00.000 / ${fmtTime(dur)}`;
        addRegionsFromModel();
      });

      // Periodic time sync during playback
      ws.on('timeupdate', (t) => {
        timeDisplay.textContent = `${fmtTime(t)} / ${fmtTime(ws.getDuration())}`;
        // Stop at play_range end
        if (_playRangeEnd !== null && t >= _playRangeEnd) {
          ws.pause();
          ws.setTime(_playRangeEnd);
          _playRangeEnd = null;
        }
      });

      // Sync current_time every 250ms during playback
      let _timeInterval = null;
      ws.on('play', () => {
        model.set('is_playing', true);
        model.save_changes();
        playPauseBtn.textContent = 'Pause';
        _timeInterval = setInterval(() => {
          model.set('current_time', ws.getCurrentTime());
          model.save_changes();
        }, 250);
      });

      ws.on('pause', () => {
        if (_timeInterval) { clearInterval(_timeInterval); _timeInterval = null; }
        model.set('is_playing', false);
        model.set('current_time', ws.getCurrentTime());
        model.save_changes();
        playPauseBtn.textContent = 'Play';
      });

      // ── Region events ──
      regionsPlugin.on('region-updated', (region) => {
        _suppressRegionSync = true;
        const updated = model.get('regions').map((r) =>
          r.id === region.id ? { ...r, start: region.start, end: region.end } : r
        );
        model.set('regions', updated);
        model.save_changes();
        _suppressRegionSync = false;
      });

      regionsPlugin.on('region-clicked', (region, e) => {
        e.stopPropagation();
        model.set('selected_region_id', region.id);
        model.set('current_time', region.start);
        model.save_changes();
        ws.setTime(region.start);
        highlightSelected(region.id);

        regionInfo.innerHTML =
          `<strong>Selected:</strong> ${region.content || region.id} ` +
          `| <strong>Time:</strong> ${fmtTime(region.start)} - ${fmtTime(region.end)} ` +
          `(${(region.end - region.start).toFixed(3)}s)`;
      });

      // ── Button handlers ──
      playPauseBtn.addEventListener('click', () => ws.playPause());

      zoomInBtn.addEventListener('click', () => {
        const z = Math.min(model.get('zoom_level') * 2, 1000);
        model.set('zoom_level', z);
        model.save_changes();
      });

      zoomOutBtn.addEventListener('click', () => {
        const z = Math.max(Math.floor(model.get('zoom_level') / 2), 10);
        model.set('zoom_level', z);
        model.save_changes();
      });

      // ── Model change listeners ──
      model.on('change:audio_data', loadAudio);

      model.on('change:regions', () => {
        if (_suppressRegionSync) return;
        addRegionsFromModel();
      });

      model.on('change:current_time', () => {
        if (!model.get('is_playing')) {
          ws.setTime(model.get('current_time'));
        }
      });

      model.on('change:selected_region_id', () => {
        highlightSelected(model.get('selected_region_id'));
      });

      model.on('change:zoom_level', () => {
        ws.zoom(model.get('zoom_level'));
      });

      model.on('change:play_range', () => {
        const range = model.get('play_range');
        if (range && range.length === 2) {
          _playRangeEnd = range[1];
          ws.setTime(range[0]);
          ws.play();
        }
      });

      model.on('change:waveform_color', () => {
        ws.setOptions({ waveColor: model.get('waveform_color') });
      });

      model.on('change:progress_color', () => {
        ws.setOptions({ progressColor: model.get('progress_color') });
      });

      return () => {
        if (_timeInterval) clearInterval(_timeInterval);
        ws.destroy();
      };
    }

    export default { render };
    """

    _css = """
    .wavesurfer-region {
      transition: opacity 0.15s ease;
    }
    .wavesurfer-region:hover {
      opacity: 0.8 !important;
    }
    """
