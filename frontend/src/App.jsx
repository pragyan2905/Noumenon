import { useState, useRef } from 'react'

const TABS = [
  { id: 'image', label: 'Image', theme: 'image' },
  { id: 'document', label: 'Document', theme: 'document' },
  { id: 'data', label: 'Data', theme: 'data' },
  { id: 'media', label: 'Media', theme: 'media' },
  { id: 'archive', label: 'Archive', theme: 'archive' },
];

const EXTENSION_MAP = {
  'image': ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif', 'pdf', 'txt'],
  'document': ['pdf', 'docx', 'png', 'jpg', 'txt'],
  'data': ['csv', 'json', 'yaml', 'yml', 'xml', 'toml', 'tsv'],
  'media': ['mp4', 'mp3', 'wav', 'mkv', 'avi', 'mov', 'aac', 'flac'],
  'archive': ['zip', 'tar', 'gz', 'bz2']
};

function App() {
  const [activeTab, setActiveTab] = useState('image');
  const [file, setFile] = useState(null);
  const [targetFormat, setTargetFormat] = useState('png');
  const [quality, setQuality] = useState(90);
  const [isConverting, setIsConverting] = useState(false);
  const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: string, url?: string, warnings?: string[] }
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setStatus(null);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus(null);
    }
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    setStatus(null);
  };

  const handleConvert = async () => {
    if (!file) return;
    
    setIsConverting(true);
    setStatus(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', targetFormat);
    
    // Add extra options based on category
    const options = {};
    if (activeTab === 'image' && ['jpg', 'jpeg', 'webp'].includes(targetFormat)) {
      options.quality = parseInt(quality, 10);
    }
    formData.append('options', JSON.stringify(options));

    try {
      const response = await fetch(window.location.origin + '/api/convert', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMsg = 'Conversion failed';
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || errorMsg;
        } catch(e) {
          errorMsg = await response.text();
        }
        throw new Error(errorMsg);
      }

      // Handle file download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'converted_file.' + targetFormat;
      
      if (contentDisposition && contentDisposition.includes('filename=')) {
        filename = contentDisposition.split('filename=')[1].replace(/"/g, '');
      }

      const warningsHeader = response.headers.get('X-Conversion-Warnings');
      let warnings = [];
      if (warningsHeader) {
         warnings = JSON.parse(warningsHeader);
      }

      setStatus({
        type: 'success',
        message: 'Conversion completed successfully!',
        url,
        filename,
        warnings
      });

    } catch (err) {
      setStatus({
        type: 'error',
        message: `${err.name}: ${err.message}`
      });
    } finally {
      setIsConverting(false);
    }
  };

  const currentOptions = EXTENSION_MAP[activeTab] || [];

  return (
    <main>
      <h1>Local<span>Convert</span></h1>
      <p className="subtitle">Private, local file conversion. Everything stays on your device.</p>

      <div className="tabs-container">
        {TABS.map(tab => (
          <button 
            key={tab.id}
            className={`tab-btn ${tab.theme} ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => {
              setActiveTab(tab.id);
              setTargetFormat(EXTENSION_MAP[tab.id][0]);
              setStatus(null);
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="converter-card">
        
        {!file ? (
          <div 
            className="upload-area" 
            onDragOver={handleDragOver} 
            onDrop={handleDrop}
            onClick={() => fileInputRef.current.click()}
          >
            <div className="upload-icon">📁</div>
            <div className="upload-text">Drag & Drop your file here</div>
            <div className="upload-subtext">or click to browse</div>
            <input 
              type="file" 
              ref={fileInputRef} 
              style={{ display: 'none' }} 
              onChange={handleFileSelect} 
            />
          </div>
        ) : (
          <div className="file-info">
            <span className="file-name">📄 {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
            <button className="remove-btn" onClick={removeFile}>✖</button>
          </div>
        )}

        <div className="controls-grid">
          <div className="control-group">
            <label>Convert To</label>
            <select 
              value={targetFormat} 
              onChange={(e) => setTargetFormat(e.target.value)}
            >
              {currentOptions.map(ext => (
                <option key={ext} value={ext}>{ext.toUpperCase()}</option>
              ))}
            </select>
          </div>

          {activeTab === 'image' && ['jpg', 'jpeg', 'webp'].includes(targetFormat) && (
            <div className="control-group">
              <label>Quality ({quality}%)</label>
              <input 
                type="range" 
                min="1" 
                max="100" 
                value={quality} 
                onChange={(e) => setQuality(e.target.value)} 
              />
            </div>
          )}
        </div>

        <button 
          className={`convert-btn theme-${activeTab}`}
          onClick={handleConvert}
          disabled={!file || isConverting}
        >
          {isConverting ? (
             <><span className="spinner"></span> Processing...</>
          ) : (
             `Convert to ${targetFormat.toUpperCase()}`
          )}
        </button>

        {status && (
          <div className={`status-box status-${status.type}`}>
            <h3>{status.type === 'success' ? '✅ Success!' : '❌ Error'}</h3>
            <p>{status.message}</p>
            
            {status.warnings && status.warnings.length > 0 && (
              <ul style={{marginBottom: '16px', paddingLeft: '20px'}}>
                {status.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            )}

            {status.type === 'success' && status.url && (
              <a 
                href={status.url} 
                download={status.filename}
                className="download-btn"
              >
                Download File
              </a>
            )}
          </div>
        )}

      </div>
    </main>
  )
}

export default App
