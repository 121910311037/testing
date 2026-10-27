const state = {
  patientId: `web-${crypto.randomUUID ? crypto.randomUUID().slice(0, 8) : Date.now()}`,
  assessment: null,
  voiceProfile: null,
  recordedBlob: null,
  recorder: null,
  recordStream: null,
};

const $ = (selector) => document.querySelector(selector);
const api = (path, options = {}) => fetch(path, options);

function showStep(name) {
  document.querySelectorAll('.step').forEach((step) => step.classList.remove('active'));
  const target = $(`#step-${name}`);
  if (target) target.classList.add('active');
  document.querySelectorAll('[data-progress]').forEach((item) => {
    const names = ['assessment', 'result', 'voice', 'test'];
    const current = names.indexOf(name);
    const index = names.indexOf(item.dataset.progress);
    item.classList.toggle('active', index === current);
    item.classList.toggle('done', index < current);
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function selected(name, fallback = '') {
  return document.querySelector(`input[name="${name}"]:checked`)?.value || fallback;
}

function displayError(element, message) {
  element.textContent = message;
  element.classList.toggle('hidden', !message);
}

function prettyEmotion(value) {
  return String(value || 'neutral').replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function riskClass(risk) {
  return String(risk || 'Low').toLowerCase();
}

function renderScores(scores = {}) {
  const target = $('#result-scores');
  target.innerHTML = Object.entries(scores)
    .sort(([, a], [, b]) => b - a)
    .map(([name, value]) => {
      const percentage = Math.round(Number(value) * 100);
      return `<div class="score-row"><span>${prettyEmotion(name)}</span><span class="score-track"><span class="score-fill" style="width:${percentage}%"></span></span><strong>${percentage}%</strong></div>`;
    }).join('');
}

function renderAssessment(result) {
  state.assessment = result;
  $('#result-emotion').textContent = prettyEmotion(result.primary_emotion);
  $('#result-confidence').textContent = `${Math.round((result.emotion_confidence || 0) * 100)}% confidence · ${prettyEmotion(result.dominant_mood)} overall mood`;
  const risk = $('#result-risk');
  risk.textContent = `${result.risk_level || 'Low'} support need`;
  risk.className = `pill ${riskClass(result.risk_level)}`;
  $('#result-action').textContent = result.recommendation.recommended_action;
  $('#result-recommendation').textContent = result.recommendation.recommendation;
  $('#result-source').textContent = result.detection_source || 'demo detector';
  renderScores(result.emotion_scores);
  const safety = $('#result-safety');
  if (result.recommendation.safety_note) {
    safety.textContent = result.recommendation.safety_note;
    safety.classList.remove('hidden');
  } else {
    safety.classList.add('hidden');
  }
  $('#test-text').value = result.recommendation.voice_script || 'It is time for your next check-in. Small steps count.';
  $('#test-tone').value = result.recommendation.voice_tone || 'supportive';
}

$('#assessment-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  displayError($('#assessment-error'), '');
  $('#assessment-submit').disabled = true;
  $('#assessment-loading').classList.remove('hidden');
  const payload = {
    patient_id: state.patientId,
    responses: {
      sleep_pattern: Number(selected('sleep', 3)),
      energy_level: Number(selected('energy', 3)),
      stress_level: Number(selected('stress', 3)),
      self_reported_feeling: selected('feeling', 'neutral'),
    },
    text: $('#check-in-text').value.trim(),
  };
  try {
    const response = await api('/api/assessments/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'We could not read the check-in.');
    renderAssessment(data);
    showStep('result');
  } catch (error) {
    displayError($('#assessment-error'), error.message);
  } finally {
    $('#assessment-submit').disabled = false;
    $('#assessment-loading').classList.add('hidden');
  }
});

$('#to-voice').addEventListener('click', () => showStep('voice'));
$('#back-to-assessment').addEventListener('click', () => showStep('assessment'));
$('#skip-voice').addEventListener('click', () => showStep('test'));

function chooseMimeType() {
  const choices = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'];
  return choices.find((type) => window.MediaRecorder && MediaRecorder.isTypeSupported(type)) || '';
}

function stopStream() {
  state.recordStream?.getTracks().forEach((track) => track.stop());
  state.recordStream = null;
}

$('#record-button').addEventListener('click', async () => {
  const button = $('#record-button');
  if (state.recorder && state.recorder.state === 'recording') {
    state.recorder.stop();
    button.textContent = '● Start recording';
    $('#record-dot').classList.remove('live');
    $('#record-title').textContent = 'Recording ready';
    $('#record-status').textContent = 'Listen back, then save your profile.';
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    $('#record-status').textContent = 'Recording is not supported here. Use the upload option instead.';
    return;
  }
  try {
    state.recordStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const chunks = [];
    const mimeType = chooseMimeType();
    state.recorder = mimeType ? new MediaRecorder(state.recordStream, { mimeType }) : new MediaRecorder(state.recordStream);
    state.recorder.addEventListener('dataavailable', (event) => { if (event.data.size) chunks.push(event.data); });
    state.recorder.addEventListener('stop', () => {
      state.recordedBlob = new Blob(chunks, { type: state.recorder.mimeType || 'audio/webm' });
      const url = URL.createObjectURL(state.recordedBlob);
      $('#recorded-audio').src = url;
      $('#recorded-audio').hidden = false;
      stopStream();
    }, { once: true });
    state.recorder.start();
    button.textContent = '■ Stop recording';
    $('#record-dot').classList.add('live');
    $('#record-title').textContent = 'Recording…';
    $('#record-status').textContent = 'Speak clearly for 10–30 seconds.';
  } catch (error) {
    stopStream();
    $('#record-status').textContent = 'Microphone permission was not granted. You can upload a sample instead.';
  }
});

function recordedFile() {
  if (!state.recordedBlob) return null;
  const extension = state.recordedBlob.type.includes('ogg') ? 'ogg' : 'webm';
  return new File([state.recordedBlob], `recorded-sample.${extension}`, { type: state.recordedBlob.type });
}

$('#sample-file').addEventListener('change', () => {
  const file = $('#sample-file').files[0];
  if (file) {
    state.recordedBlob = null;
    $('#recorded-audio').src = URL.createObjectURL(file);
    $('#recorded-audio').hidden = false;
    $('#record-status').textContent = `${file.name} selected.`;
  }
});

$('#save-voice').addEventListener('click', async () => {
  displayError($('#voice-error'), '');
  $('#voice-success').classList.add('hidden');
  const consent = $('#voice-consent').checked;
  const sample = $('#sample-file').files[0] || recordedFile();
  if (!consent) return displayError($('#voice-error'), 'Please confirm that you have permission to use this voice.');
  if (!sample) return displayError($('#voice-error'), 'Please record or upload a voice sample before continuing.');
  const button = $('#save-voice');
  button.disabled = true;
  button.textContent = 'Saving profile…';
  try {
    const form = new FormData();
    form.append('patient_id', state.patientId);
    form.append('profile_name', $('#profile-name').value.trim() || 'My voice');
    form.append('speaker_name', $('#speaker-name').value.trim() || 'My voice');
    form.append('language', $('#voice-language').value);
    form.append('consent_confirmed', 'true');
    const createdResponse = await api('/api/voice-profiles/', { method: 'POST', body: form });
    const created = await createdResponse.json();
    if (!createdResponse.ok) throw new Error(created.detail || 'The voice profile could not be created.');
    const samples = new FormData();
    samples.append('file', sample, sample.name || 'voice-sample.webm');
    const sampleResponse = await api(`/api/voice-profiles/${created.id}/samples`, { method: 'POST', body: samples });
    const saved = await sampleResponse.json();
    if (!sampleResponse.ok) throw new Error(saved.detail || 'The sample could not be saved.');
    state.voiceProfile = saved;
    $('#profile-details').textContent = `${saved.speaker_name} · ${saved.sample_count} sample saved · consent confirmed`;
    $('#profile-status').textContent = saved.provider === 'xtts' ? 'Cloned voice ready' : 'Profile saved';
    $('#test-notice').textContent = saved.test_notice;
    $('#test-notice').className = 'alert info';
    showStep('test');
  } catch (error) {
    displayError($('#voice-error'), error.message);
  } finally {
    button.disabled = false;
    button.innerHTML = 'Save profile and continue <span aria-hidden="true">→</span>';
  }
});

$('#test-button').addEventListener('click', async () => {
  displayError($('#test-error'), '');
  if (!state.voiceProfile?.id) {
    displayError($('#test-error'), 'Save a voice profile first. You can go back and set one up.');
    return;
  }
  const button = $('#test-button');
  button.disabled = true;
  button.textContent = 'Preparing test…';
  $('#browser-speech').classList.add('hidden');
  try {
    const form = new FormData();
    form.append('text', $('#test-text').value.trim());
    form.append('tone', $('#test-tone').value);
    const response = await api(`/api/voice-profiles/${state.voiceProfile.id}/test`, { method: 'POST', body: form });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'The voice test could not be generated.');
    $('#test-notice').textContent = result.notice;
    $('#test-notice').className = `alert ${result.cloned ? 'success' : 'info'}`;
    const audio = $('#test-audio');
    if (result.audio_url) {
      audio.src = result.audio_url;
      audio.hidden = false;
      audio.load();
    } else {
      audio.hidden = true;
    }
    if (!result.cloned && window.speechSynthesis) $('#browser-speech').classList.remove('hidden');
  } catch (error) {
    displayError($('#test-error'), error.message);
  } finally {
    button.disabled = false;
    button.innerHTML = 'Test profile <span aria-hidden="true">▶</span>';
  }
});

$('#browser-speech').addEventListener('click', () => {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance($('#test-text').value);
  utterance.rate = $('#test-tone').value === 'calm' ? .88 : 1;
  window.speechSynthesis.speak(utterance);
});

$('#start-over').addEventListener('click', () => {
  state.assessment = null;
  state.voiceProfile = null;
  state.recordedBlob = null;
  $('#assessment-form').reset();
  $('#recorded-audio').hidden = true;
  $('#sample-file').value = '';
  $('#voice-consent').checked = false;
  showStep('assessment');
});
