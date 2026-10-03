import { useState, useRef, useEffect } from 'react'

const TABS = [
  { id: 'image', label: 'Image Processing', desc: 'Resize, rotate, grayscale, & convert', theme: 'image' },
  { id: 'document', label: 'Document Tools', desc: 'PDF encryption, extraction, & conversion', theme: 'document' },
  { id: 'data', label: 'Data Conversion', desc: 'Excel, Parquet, JSON, CSV & more', theme: 'data' },
  { id: 'media', label: 'Media Encoding', desc: 'Video & audio format conversion', theme: 'media' },
  { id: 'archive', label: 'Archive Utilities', desc: 'Zip, Tar, Extract & Repack', theme: 'archive' },
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
  const [files, setFiles] = useState([]);
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
  
  const [imgBrightness, setImgBrightness] = useState(100);
  const [imgContrast, setImgContrast] = useState(100);
  const [imgSharpness, setImgSharpness] = useState(100);
  const [imgAutoContrast, setImgAutoContrast] = useState(false);
  const [imgFlip, setImgFlip] = useState('');
  const [imgNoiseReduction, setImgNoiseReduction] = useState('');
  const [imgCompressLevel, setImgCompressLevel] = useState('');
  const [imgRemoveBackground, setImgRemoveBackground] = useState(false);
  
  // Advanced PDF Options
  const [pdfPassword, setPdfPassword] = useState('');
  const [pdfEncryptPassword, setPdfEncryptPassword] = useState('');
  const [pdfPage, setPdfPage] = useState('');
  const [pdfRotate, setPdfRotate] = useState('');
  const [pdfAction, setPdfAction] = useState('');
  const [pdfCompressLevel, setPdfCompressLevel] = useState('');
  const [pdfWatermark, setPdfWatermark] = useState('');

  const [isConverting, setIsConverting] = useState(false);
  const [status, setStatus] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => e.preventDefault();

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)]);
      setStatus(null);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(prev => [...prev, ...Array.from(e.target.files)]);
      setStatus(null);
    }
    // Clear the input so the same file can be selected again if needed
    e.target.value = '';
  };

  const removeFile = (index) => {
    if (index !== undefined) {
      setFiles(prev => {
        const newFiles = [...prev];
        newFiles.splice(index, 1);
        return newFiles;
      });
    } else {
      setFiles([]);
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
    setStatus(null);
  };

  const handleConvert = async () => {
    if (files.length === 0) return;
    
    setIsConverting(true);
    setStatus(null);

    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
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
      if (imgBrightness && imgBrightness !== 100) options.brightness = parseInt(imgBrightness, 10);
      if (imgContrast && imgContrast !== 100) options.contrast = parseInt(imgContrast, 10);
      if (imgSharpness && imgSharpness !== 100) options.sharpness = parseInt(imgSharpness, 10);
      if (imgAutoContrast) options.auto_contrast = true;
      if (imgFlip) options.flip = imgFlip;
      if (imgNoiseReduction) options.noise_reduction = imgNoiseReduction;
      if (imgCompressLevel) options.compress_level = imgCompressLevel;
      if (imgRemoveBackground) options.remove_background = true;
    }
    
    if (activeTab === 'document') {
      if (pdfPassword) options.password = pdfPassword;
      if (pdfEncryptPassword) options.encrypt_password = pdfEncryptPassword;
      if (pdfPage) options.page = pdfPage;
      if (pdfRotate) options.rotate = parseInt(pdfRotate, 10);
      if (pdfAction) options.action = pdfAction;
      if (pdfCompressLevel) options.compress_level = pdfCompressLevel;
      if (pdfWatermark) options.watermark = pdfWatermark;
    }

    formData.append('options', JSON.stringify(options));

    try {
      const response = await fetch(window.location.origin + '/api/convert', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMsg = 'Conversion failed';
        const errorText = await response.text();
        try {
          const errorData = JSON.parse(errorText);
          errorMsg = errorData.detail || errorMsg;
        } catch(e) {
          errorMsg = errorText || errorMsg;
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

      const originalTotalSize = files.reduce((acc, f) => acc + f.size, 0);
      const newSize = blob.size;
      const sizeDiffStr = ((1 - (newSize / originalTotalSize)) * 100).toFixed(1);
      const isReduction = newSize < originalTotalSize;

      setStatus({
        type: 'success',
        message: 'Conversion completed successfully!',
        url,
        filename,
        warnings,
        originalSize: (originalTotalSize / 1024 / 1024).toFixed(2),
        newSize: (newSize / 1024 / 1024).toFixed(2),
        compressionRatio: sizeDiffStr,
        isReduction
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
            <h1>Nou<span>menon</span></h1>
            <p className="subtitle">Private, local file conversion. Everything stays on your device.</p>
          </div>
          <button 
            onClick={() => setIsDarkMode(!isDarkMode)}
            style={{ background: 'none', border: '1px solid var(--border-color)', borderRadius: '4px', padding: '5px 10px', cursor: 'pointer', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-main)', fontWeight: 'bold' }}
            title="Toggle Dark Mode"
          >
            {isDarkMode ? 'Light Mode' : 'Dark Mode'}
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
              <h3 style={{ margin: '0 0 5px 0' }}>{tab.label}</h3>
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
          style={{ background: 'none', border: '1px solid var(--border-color)', borderRadius: '4px', padding: '5px 10px', cursor: 'pointer', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-main)', fontWeight: 'bold' }}
          title="Toggle Dark Mode"
        >
          {isDarkMode ? 'Light Mode' : 'Dark Mode'}
        </button>
      </div>
      
      <h1>{TABS.find(t => t.id === activeTab).label} <span>Workspace</span></h1>

      <div className="converter-card">
        
        {/* Hidden persistent file input */}
        <input 
          type="file" 
          multiple
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          onChange={handleFileSelect} 
        />

        {files.length === 0 ? (
          <div 
            className="upload-area" 
            onDragOver={handleDragOver} 
            onDrop={handleDrop}
            onClick={() => fileInputRef.current.click()}
          >
            <div className="upload-icon" style={{ fontWeight: 'bold', color: 'var(--text-muted)' }}>+</div>
            <div className="upload-text">Drag & Drop your files here</div>
            <div className="upload-subtext">or click to browse</div>
          </div>
        ) : (
          <div className="file-info-container">
            {files.map((f, i) => (
              <div key={i} className="file-info" style={{ marginBottom: '10px' }}>
                <span className="file-name">{f.name} ({(f.size / 1024 / 1024).toFixed(2)} MB)</span>
                <button className="remove-btn" onClick={() => removeFile(i)}>✖</button>
              </div>
            ))}
            <button onClick={(e) => { e.preventDefault(); fileInputRef.current.click(); }} style={{ background: 'none', border: '1px dashed #ccc', padding: '10px', width: '100%', cursor: 'pointer', marginBottom: '20px', borderRadius: '4px' }}>+ Add More Files</button>
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
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Compress Level</label>
                <select value={imgCompressLevel} onChange={(e) => setImgCompressLevel(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}>
                  <option value="">Standard (Default)</option>
                  <option value="high">High Compression (Lowest Size)</option>
                </select>
              </div>

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

              <div className="control-group">
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Flip Image</label>
                <select value={imgFlip} onChange={(e) => setImgFlip(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}>
                  <option value="">None</option>
                  <option value="horizontal">Horizontal (Mirror)</option>
                  <option value="vertical">Vertical</option>
                </select>
              </div>

              <div className="control-group">
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Noise Reduction</label>
                <select value={imgNoiseReduction} onChange={(e) => setImgNoiseReduction(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}>
                  <option value="">None</option>
                  <option value="median">Median Filter (Despeckle)</option>
                  <option value="gaussian">Gaussian Blur (Smooth)</option>
                </select>
              </div>

              <div className="control-group" style={{ gridColumn: '1 / -1' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Brightness</span> <span>{imgBrightness}%</span>
                </label>
                <input type="range" min="10" max="300" value={imgBrightness} onChange={(e) => setImgBrightness(e.target.value)} style={{ width: '100%' }} />
              </div>

              <div className="control-group" style={{ gridColumn: '1 / -1' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Contrast</span> <span>{imgContrast}%</span>
                </label>
                <input type="range" min="10" max="300" value={imgContrast} onChange={(e) => setImgContrast(e.target.value)} style={{ width: '100%' }} />
              </div>

              <div className="control-group" style={{ gridColumn: '1 / -1' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 'bold', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Sharpness</span> <span>{imgSharpness}%</span>
                </label>
                <input type="range" min="10" max="500" value={imgSharpness} onChange={(e) => setImgSharpness(e.target.value)} style={{ width: '100%' }} />
              </div>

              <div className="control-group" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <input type="checkbox" id="grayscale" checked={imgGrayscale} onChange={(e) => setImgGrayscale(e.target.checked)} />
                <label htmlFor="grayscale" style={{ fontSize: '0.8rem', margin: 0, fontWeight: 'bold', cursor: 'pointer' }}>Convert to Grayscale</label>
              </div>

              <div className="control-group" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <input type="checkbox" id="metadata" checked={imgRemoveMetadata} onChange={(e) => setImgRemoveMetadata(e.target.checked)} />
                <label htmlFor="metadata" style={{ fontSize: '0.8rem', margin: 0, fontWeight: 'bold', cursor: 'pointer' }}>Strip EXIF Metadata</label>
              </div>

              <div className="control-group" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <input type="checkbox" id="autocontrast" checked={imgAutoContrast} onChange={(e) => setImgAutoContrast(e.target.checked)} />
                <label htmlFor="autocontrast" style={{ fontSize: '0.8rem', margin: 0, fontWeight: 'bold', cursor: 'pointer' }}>Auto-Contrast</label>
              </div>

              <div className="control-group" style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(59, 130, 246, 0.1)', padding: '10px', borderRadius: '4px', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                <input type="checkbox" id="removebg" checked={imgRemoveBackground} onChange={(e) => setImgRemoveBackground(e.target.checked)} />
                <label htmlFor="removebg" style={{ fontSize: '0.8rem', margin: 0, fontWeight: 'bold', cursor: 'pointer', color: '#1d4ed8' }}>✨ AI Background Removal (Slow)</label>
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
                    <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Batch Action</label>
                    <select value={pdfAction} onChange={(e) => setPdfAction(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}>
                      <option value="">None</option>
                      <option value="merge">Merge Multiple PDFs</option>
                    </select>
                  </div>
                  
                  <div className="control-group">
                    <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Compress Level</label>
                    <select value={pdfCompressLevel} onChange={(e) => setPdfCompressLevel(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}>
                      <option value="">Standard (Default)</option>
                      <option value="high">High Compression (Lower Quality)</option>
                    </select>
                  </div>

                  <div className="control-group" style={{ gridColumn: '1 / -1' }}>
                    <label style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Text Watermark</label>
                    <input type="text" value={pdfWatermark} onChange={(e) => setPdfWatermark(e.target.value)} placeholder="Enter text to watermark..." style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} />
                  </div>

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
          disabled={files.length === 0 || isConverting}
        >
          {isConverting ? (
             <><span className="spinner"></span> Processing...</>
          ) : (
             `Execute Operations`
          )}
        </button>

        {status && (
          <div className={`status-box status-${status.type}`}>
            <h3>{status.type === 'success' ? 'Success!' : 'Error'}</h3>
            <p>{status.message}</p>
            
            {status.type === 'success' && status.originalSize && (
              <div style={{ background: 'rgba(0,0,0,0.05)', padding: '10px', borderRadius: '4px', marginBottom: '15px', fontSize: '0.9rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span>Original Size:</span>
                  <strong>{status.originalSize} MB</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span>Final Size:</span>
                  <strong>{status.newSize} MB</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: status.isReduction ? 'green' : 'red' }}>
                  <span>Size Difference:</span>
                  <strong>{status.isReduction ? '-' : '+'}{Math.abs(status.compressionRatio)}%</strong>
                </div>
              </div>
            )}

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
