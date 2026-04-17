# Email Verification Code 


## Step 1: Add New States

Add these states inside the `SignUp` component (after existing states):
```javascript
// Verification states
const [showVerification, setShowVerification] = useState(false);
const [verificationCode, setVerificationCode] = useState('');
const [userInputCode, setUserInputCode] = useState(['', '', '', '', '', '']);
const [pendingUser, setPendingUser] = useState(null);
```

---

## Step 2: Add New Functions

Add these functions after the `validateEmail` function:
```javascript
// Generate 6-digit code
const generateCode = () => {
  return Math.floor(100000 + Math.random() * 900000).toString();
};

// Handle verification code input
const handleCodeInput = (index, value) => {
  if (value.length > 1) return;
  if (value && !/^\d$/.test(value)) return;
  
  const newCode = [...userInputCode];
  newCode[index] = value;
  setUserInputCode(newCode);
  
  // Auto-focus next input
  if (value && index < 5) {
    const nextInput = document.getElementById(`code-${index + 1}`);
    if (nextInput) nextInput.focus();
  }
};

// Handle backspace in code input
const handleCodeKeyDown = (index, e) => {
  if (e.key === 'Backspace' && !userInputCode[index] && index > 0) {
    const prevInput = document.getElementById(`code-${index - 1}`);
    if (prevInput) prevInput.focus();
  }
};

// Verify the code
const handleVerifyCode = async () => {
  const enteredCode = userInputCode.join('');
  
  if (enteredCode === verificationCode) {
    setLoading(true);
    try {
      await window.storage.set(`user:${pendingUser.email}`, JSON.stringify(pendingUser));
      setSuccess('Account verified successfully! Redirecting to sign in...');
      setTimeout(() => {
        onSwitchToSignIn();
      }, 2000);
    } catch (err) {
      setError('Failed to create account. Please try again.');
    }
    setLoading(false);
  } else {
    setError('Invalid verification code. Please try again.');
    setUserInputCode(['', '', '', '', '', '']);
  }
};

// Resend code
const handleResendCode = () => {
  const newCode = generateCode();
  setVerificationCode(newCode);
  setUserInputCode(['', '', '', '', '', '']);
  setError('');
  setSuccess('New verification code sent!');
  // TODO: Send new code via email here
};
```

---

## Step 3: Modify handleSubmit Function

Replace the end of `handleSubmit` function.

### Remove this:
```javascript
try {
  await window.storage.set(`user:${email.toLowerCase()}`, JSON.stringify(user));
  setSuccess('Account created successfully! Redirecting to sign in...');
  setTimeout(() => {
    onSwitchToSignIn();
  }, 2000);
} catch (err) {
  setError('Failed to create account. Please try again.');
}
setLoading(false);
```

### Replace with:
```javascript
// Generate verification code and show verification screen
const code = generateCode();
setVerificationCode(code);
setPendingUser(user);
setShowVerification(true);
setLoading(false);

// TODO: Send code via email here
// Example: await sendVerificationEmail(email, code);
```

---

## Step 4: Add Verification Screen

Add this code before the main `return` statement in the SignUp component:
```javascript
// Verification Screen
if (showVerification) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 flex items-center justify-center p-4 relative">
      <GridBackground />
      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-500 mb-4 shadow-lg shadow-green-500/25">
            <Mail className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Verify Your Email</h1>
          <p className="text-slate-400">We sent a verification code to</p>
          <p className="text-blue-400 font-medium">{email}</p>
        </div>
        
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-8 border border-slate-700/50 shadow-2xl">
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm flex items-center gap-2">
              <XCircle className="w-4 h-4" />
              {error}
            </div>
          )}
          
          {success && (
            <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-xl text-green-400 text-sm flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              {success}
            </div>
          )}
          
          <div className="space-y-6">
            <div>
              <label className="block text-slate-300 text-sm font-medium mb-4 text-center">Enter 6-digit code</label>
              <div className="flex justify-center gap-2">
                {[0, 1, 2, 3, 4, 5].map((index) => (
                  <input
                    key={index}
                    id={`code-${index}`}
                    type="text"
                    maxLength={1}
                    value={userInputCode[index]}
                    onChange={(e) => handleCodeInput(index, e.target.value)}
                    onKeyDown={(e) => handleCodeKeyDown(index, e)}
                    className="w-12 h-14 text-center text-2xl font-bold bg-slate-900/50 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                  />
                ))}
              </div>
            </div>
            
            <button
              onClick={handleVerifyCode}
              disabled={loading || userInputCode.join('').length !== 6}
              className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-xl hover:from-green-400 hover:to-emerald-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-green-500/25"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>Verify Account <CheckCircle className="w-5 h-5" /></>
              )}
            </button>
            
            <div className="text-center">
              <p className="text-slate-500 text-sm">
                Didn't receive the code?{' '}
                <button onClick={handleResendCode} className="text-blue-400 hover:text-blue-300 font-medium transition-colors">
                  Resend
                </button>
              </p>
            </div>
          </div>
          
          <div className="mt-6 text-center">
            <button 
              onClick={() => setShowVerification(false)} 
              className="text-slate-500 hover:text-slate-300 text-sm transition-colors"
            >
              ← Back to Sign Up
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Component Structure
```
SignUp Component
├── States
│   ├── name, email, password, confirmPassword (existing)
│   ├── showVerification      ← NEW
│   ├── verificationCode      ← NEW
│   ├── userInputCode         ← NEW
│   └── pendingUser           ← NEW
├── Functions
│   ├── validatePassword()    (existing)
│   ├── validateEmail()       (existing)
│   ├── generateCode()        ← NEW
│   ├── handleCodeInput()     ← NEW
│   ├── handleCodeKeyDown()   ← NEW
│   ├── handleVerifyCode()    ← NEW
│   ├── handleResendCode()    ← NEW
│   └── handleSubmit()        ← MODIFIED
├── if (showVerification)     ← NEW
│   └── return <VerificationScreen />
└── return <SignUpForm />     (existing)
```

