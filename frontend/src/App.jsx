import { useState, useRef, useEffect } from 'react'

const TABS = [
  { id: 'image', label: 'Image Processing', desc: 'Resize, rotate, grayscale, & convert', theme: 'image', icon: '🖼️' },
  { id: 'document', label: 'Document Tools', desc: 'PDF encryption, extraction, & conversion', theme: 'document', icon: '📄' },
  { id: 'data', label: 'Data Conversion', desc: 'Excel, Parquet, JSON, CSV & more', theme: 'data', icon: '📊' },
  { id: 'media', label: 'Media Encoding', desc: 'Video & audio format conversion', theme: 'media', icon: '🎵' },
  { id: 'archive', label: 'Archive Utilities', desc: 'Zip, Tar, Extract & Repack', theme: 'archive', icon: '📦' },
];

const EXTENSION_MAP = {
  'image': ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif', 'pdf', 'txt'],
  'document': ['pdf', 'docx', 'png', 'jpg', 'txt', 'md', 'html'],
  'data': ['csv', 'json', 'yaml', 'yml', 'xml', 'toml', 'tsv', 'xlsx', 'parquet'],
  'media': ['mp4', 'mp3', 'wav', 'mkv', 'avi', 'mov', 'aac', 'flac'],
  'archive': ['zip', 'tar', 'gz', 'bz2']
};

function App() {
  const [activeTab, setActiveTab] = useState(null); // null = Home Dashboard
  const [file, setFile] = useState(null);
  const [targetFormat, setTargetFormat] = useState('png');
  const [quality, setQuality] = useState(90);
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [isDarkMode]);
  
  // Advanced Image Options
  const [imgScale, setImgScale] = useState(100);
  const [imgWidth, setImgWidth] = useState('');
  const [imgHeight, setImgHeight] = useState('');
  const [imgRotate, setImgRotate] = useState('');
  const [imgGrayscale, setImgGrayscale] = useState(false);
  const [imgRemoveMetadata, setImgRemoveMetadata] = useState(true);
  const [imgDpi, setImgDpi] = useState('');
  
  // Advanced PDF Options
  const [pdfPassword, setPdfPassword] = useState('');
  const [pdfEncryptPassword, setPdfEncryptPassword] = useState('');
  const [pdfPage, setPdfPage] = useState('');
  const [pdfRotate, setPdfRotate] = useState('');

  const [isConverting, setIsConverting] = useState(false);
  const [status, setStatus] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => e.preventDefault();

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
    if (activeTab === 'image') {
      if (['jpg', 'jpeg', 'webp'].includes(targetFormat)) {
        options.quality = parseInt(quality, 10);
      }
      if (imgScale && imgScale !== 100) options.scale = parseInt(imgScale, 10);
      if (imgWidth) options.width = parseInt(imgWidth, 10);
      if (imgHeight) options.height = parseInt(imgHeight, 10);
      if (imgRotate) options.rotate = parseInt(imgRotate, 10);
      if (imgGrayscale) options.grayscale = true;
      if (imgRemoveMetadata) options.remove_metadata = true;
      if (imgDpi) options.dpi = parseInt(imgDpi, 10);
    }
    
    if (activeTab === 'document') {
      if (pdfPassword) options.password = pdfPassword;
      if (pdfEncryptPassword) options.encrypt_password = pdfEncryptPassword;
      if (pdfPage) options.page = pdfPage;
      if (pdfRotate) options.rotate = parseInt(pdfRotate, 10);
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

  const currentOptions = activeTab ? EXTENSION_MAP[activeTab] : [];

  if (!activeTab) {
    return (
      <main>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <h1>Local<span>Convert</span></h1>
            <p className="subtitle">Private, local file conversion. Everything stays on your device.</p>
          </div>
          <button 
            onClick={() => setIsDarkMode(!isDarkMode)}
            style={{ background: 'none', border: '1px solid var(--border-color)', borderRadius: '50%', width: '40px', height: '40px', cursor: 'pointer', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-main)' }}
            title="Toggle Dark Mode"
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
        </div>
        
        <div className="dashboard-grid">
          {TABS.map(tab => (
            <div 
              key={tab.id} 
              className={`dashboard-card ${tab.theme}`}
              onClick={() => {
                setActiveTab(tab.id);
                setTargetFormat(EXTENSION_MAP[tab.id][0]);
                setStatus(null);
              }}
            >
              <div style={{ fontSize: '3rem', marginBottom: '10px' }}>{tab.icon}</div>
              <h3>{tab.label}</h3>
              <p>{tab.desc}</p>
            </div>
          ))}
        </div>
      </main>
    );
  }

  return (
    <main>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <button className="back-btn" onClick={() => { setActiveTab(null); removeFile(); }} style={{ margin: 0 }}>
          ← Back to Tools
        </button>
        <button 
          onClick={() => setIsDarkMode(!isDarkMode)}
          style={{ background: 'none', border: '1px solid var(--border-color)', borderRadius: '50%', width: '40px', height: '40px', cursor: 'pointer', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-main)' }}
          title="Toggle Dark Mode"
        >
          {isDarkMode ? '☀️' : '🌙'}
        </button>
      </div>
      
      <h1>{TABS.find(t => t.id === activeTab).label} <span>Workspace</span></h1>

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
        </div>

        {/* ALWAYS VISIBLE ADVANCED IMAGE OPTIONS */}
        {activeTab === 'image' && (
          <div className="image-options-container" style={{ marginTop: '1rem', padding: '1rem', background: 'var(--card-bg)', borderRadius: '8px', border: '1px solid #eae6df', marginBottom: '1rem' }}>
            <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: '#666' }}>Advanced Image Options</h4>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <div className="control-group">
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Scale (%)</label>
                <input type="number" min="1" max="500" value={imgScale} onChange={(e) => { setImgScale(e.target.value); setImgWidth(''); setImgHeight(''); }} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} />
              </div>
              
              <div className="control-group">
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Custom Width & Height (px)</label>
                <div style={{ display: 'flex', gap: '5px' }}>
                  <input type="number" placeholder="W" value={imgWidth} onChange={(e) => { setImgWidth(e.target.value); setImgScale(100); }} style={{ width: '50%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} />
                  <input type="number" placeholder="H" value={imgHeight} onChange={(e) => { setImgHeight(e.target.value); setImgScale(100); }} style={{ width: '50%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} />
                </div>
              </div>

              <div className="control-group">
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Rotate</label>
                <select value={imgRotate} onChange={(e) => setImgRotate(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}>
                  <option value="">No Rotation</option>
                  <option value="90">90° Clockwise</option>
                  <option value="180">180°</option>
                  <option value="270">90° Counter-Clockwise</option>
                </select>
              </div>

              <div className="control-group">
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>DPI (Resolution)</label>
                <input type="number" placeholder="e.g. 300" value={imgDpi} onChange={(e) => setImgDpi(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} />
              </div>

              <div className="control-group" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <input type="checkbox" id="grayscale" checked={imgGrayscale} onChange={(e) => setImgGrayscale(e.target.checked)} />
                <label htmlFor="grayscale" style={{ fontSize: '0.8rem', margin: 0, fontWeight: 'bold', cursor: 'pointer' }}>Convert to Grayscale</label>
              </div>

              <div className="control-group" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <input type="checkbox" id="metadata" checked={imgRemoveMetadata} onChange={(e) => setImgRemoveMetadata(e.target.checked)} />
                <label htmlFor="metadata" style={{ fontSize: '0.8rem', margin: 0, fontWeight: 'bold', cursor: 'pointer' }}>Strip EXIF Metadata</label>
              </div>
              
              {['jpg', 'jpeg', 'webp'].includes(targetFormat) && (
                <div className="control-group" style={{ gridColumn: '1 / -1' }}>
                  <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Quality / Compression ({quality}%)</label>
                  <input 
                    type="range" min="1" max="100" value={quality} onChange={(e) => setQuality(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* ALWAYS VISIBLE ADVANCED PDF OPTIONS */}
        {activeTab === 'document' && (
          <div className="pdf-options-container" style={{ marginTop: '1rem', padding: '1rem', background: 'var(--card-bg)', borderRadius: '8px', border: '1px solid #eae6df', marginBottom: '1rem' }}>
            <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: '#666' }}>Advanced Document Options</h4>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <div className="control-group">
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Unlock Password (if encrypted)</label>
                <input type="password" value={pdfPassword} onChange={(e) => setPdfPassword(e.target.value)} placeholder="File password" style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} />
              </div>
              
              {targetFormat === 'pdf' && (
                <div className="control-group">
                  <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Encrypt Output Password</label>
                  <input type="password" value={pdfEncryptPassword} onChange={(e) => setPdfEncryptPassword(e.target.value)} placeholder="New password" style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} />
                </div>
              )}

              {targetFormat === 'pdf' && (
                <>
                  <div className="control-group">
                    <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Extract Single Page</label>
                    <input type="number" min="1" value={pdfPage} onChange={(e) => setPdfPage(e.target.value)} placeholder="e.g. 1" style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} />
                  </div>
                  
                  <div className="control-group">
                    <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Rotate Document</label>
                    <select value={pdfRotate} onChange={(e) => setPdfRotate(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}>
                      <option value="">No Rotation</option>
                      <option value="90">90° Clockwise</option>
                      <option value="180">180°</option>
                      <option value="270">90° Counter-Clockwise</option>
                    </select>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        <button 
          className={`convert-btn theme-${activeTab}`}
          onClick={handleConvert}
          disabled={!file || isConverting}
        >
          {isConverting ? (
             <><span className="spinner"></span> Processing...</>
          ) : (
             `Execute Operations`
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
