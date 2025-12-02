# 🧪 Testing Guide - New Frontend

## ✅ Servers Running

Both servers are now running:
- **Frontend**: http://localhost:8080
- **MCP Server**: http://localhost:5000

---

## 🎯 Test Checklist

### 1. Login Page ✅
- [ ] Open http://localhost:8080
- [ ] See modern dark-themed login page
- [ ] See "Study Assistant" title with gradient
- [ ] See Google sign-in button with icon
- [ ] Button has hover effect

### 2. Google Authentication
- [ ] Click "Sign in with Google"
- [ ] Redirected to Google OAuth page
- [ ] Authorize the app
- [ ] Redirected back to main app (not login page)
- [ ] See main app interface

### 3. Main App Layout
- [ ] See header with logo and calendar button
- [ ] See upload section in center
- [ ] See 4 feature buttons below upload:
  - 💬 Chatbot
  - 📝 Summary
  - ❓ Quiz
  - 🎴 Flashcards
- [ ] All buttons equally spaced in grid
- [ ] Calendar button in top-right corner

### 4. File Upload
- [ ] Click upload section
- [ ] File picker opens
- [ ] Select a PDF or audio file
- [ ] See file name and size displayed
- [ ] See progress bar animate
- [ ] See "Upload complete!" message
- [ ] See success status message

**Alternative: Drag & Drop**
- [ ] Drag a file over upload section
- [ ] Section highlights (border changes to blue)
- [ ] Drop file
- [ ] Upload starts automatically

### 5. Chatbot Feature (NEW!)
- [ ] Upload a file first
- [ ] Click "💬 Chatbot" button
- [ ] Button highlights (active state)
- [ ] Chat interface appears below
- [ ] See welcome message from assistant
- [ ] Type a question in input box
- [ ] Press Enter or click Send
- [ ] See your message appear (blue, right side)
- [ ] See loading spinner
- [ ] See assistant response (purple, left side)
- [ ] Response is relevant to uploaded document
- [ ] Try multiple questions
- [ ] Conversation history maintained

**Example Questions to Test**:
- "What is this document about?"
- "Summarize the main points"
- "Explain [specific topic from your document]"
- "What are the key takeaways?"

### 6. Summary Feature
- [ ] Upload a file
- [ ] Click "📝 Summary" button
- [ ] See loading spinner
- [ ] See "Generating summary..." status
- [ ] Summary appears in results section
- [ ] Summary is formatted nicely
- [ ] Page scrolls to results

### 7. Quiz Feature
- [ ] Upload a file
- [ ] Click "❓ Quiz" button
- [ ] See loading spinner
- [ ] Quiz questions appear
- [ ] Click an answer option
- [ ] See if answer is correct/incorrect
- [ ] Try multiple questions

### 8. Flashcards Feature
- [ ] Upload a file
- [ ] Click "🎴 Flashcards" button
- [ ] See loading spinner
- [ ] Flashcards appear in grid
- [ ] Click a flashcard
- [ ] Card flips to show answer
- [ ] Click again to flip back
- [ ] Try multiple cards

### 9. Calendar Feature
- [ ] Click "📅 Calendar" button (top-right)
- [ ] If not authenticated: redirects to Google OAuth
- [ ] After auth: calendar events appear
- [ ] Events show date, time, location
- [ ] Today's events highlighted
- [ ] Scrolls to results section

### 10. Responsive Design
- [ ] Resize browser window
- [ ] Layout adapts to smaller screens
- [ ] Buttons stack vertically on mobile
- [ ] Text remains readable
- [ ] No horizontal scrolling

### 11. Dark Theme
- [ ] Background is dark navy/slate
- [ ] Text is light and readable
- [ ] Buttons have blue/purple accents
- [ ] Hover effects work smoothly
- [ ] No harsh white backgrounds

---

## 🐛 Known Issues to Check

### Authentication
- [ ] After OAuth, should go to main app (not login page)
- [ ] Refresh page - should stay in main app
- [ ] Calendar access works without re-auth

### File Upload
- [ ] Progress bar animates smoothly
- [ ] Large files (>10MB) upload successfully
- [ ] Error handling for unsupported file types

### Chatbot
- [ ] Responses are relevant to document
- [ ] No errors in browser console
- [ ] Loading indicator disappears after response
- [ ] Chat scrolls to latest message

### General
- [ ] No console errors
- [ ] All buttons clickable
- [ ] Status messages disappear after 5 seconds
- [ ] Smooth scrolling to results

---

## 🔍 Browser Console Checks

Open browser console (F12) and check for:

### Expected Logs
```
✅ OAuth authentication successful, showing calendar
Calling displayCalendar...
Calendar events response status: 200
```

### No Errors
- No 404 errors
- No CORS errors
- No JavaScript errors
- No missing resources

---

## 📊 Test Results Template

Copy this and fill in your results:

```
## Test Results - [Date]

### Login & Auth
- Login page: ✅/❌
- Google OAuth: ✅/❌
- Redirect to main app: ✅/❌

### File Upload
- Click to upload: ✅/❌
- Drag & drop: ✅/❌
- Progress bar: ✅/❌

### Features
- Chatbot: ✅/❌
- Summary: ✅/❌
- Quiz: ✅/❌
- Flashcards: ✅/❌
- Calendar: ✅/❌

### UI/UX
- Dark theme: ✅/❌
- Responsive: ✅/❌
- Smooth animations: ✅/❌

### Issues Found
1. [Issue description]
2. [Issue description]

### Notes
[Any additional observations]
```

---

## 🚀 Quick Test Commands

### Check Server Status
```bash
# Frontend
curl -I http://localhost:8080

# MCP Server
curl http://localhost:5000/health
```

### View Server Logs
```bash
# Frontend logs (Terminal 3)
# MCP Server logs (Terminal 5)
```

### Restart Servers
```bash
# Stop MCP Server
./stop_mcp_server.sh

# Start MCP Server
./start_mcp_server.sh

# Frontend (Ctrl+C in terminal, then restart)
cd frontend && python -m http.server 8080
```

---

## 📝 Testing Tips

1. **Test in order** - Start with login, then upload, then features
2. **Use real files** - Test with actual PDFs and audio files
3. **Check console** - Keep browser console open for errors
4. **Test edge cases** - Large files, empty inputs, rapid clicks
5. **Test all features** - Don't skip any feature
6. **Document issues** - Note any bugs or unexpected behavior

---

## ✨ What to Look For

### Good Signs ✅
- Smooth animations
- Fast response times
- Clear error messages
- Intuitive navigation
- Professional appearance

### Red Flags ❌
- Console errors
- Broken layouts
- Slow loading
- Confusing UI
- Missing features

---

**Happy Testing!** 🎉

If you find any issues, please document them and we'll fix them together.

