/**
 * Event Handler Audit System
 * ==========================
 * Validates UI elements correctly respond to all user interactions.
 * Implements robust event handling per Global Rules requirements.
 * 
 * Usage: node event-handler-audit.js [path]
 */

const fs = require('fs')
const path = require('path')

const FRONTEND_PATH = process.argv[2] || path.join(__dirname, '../../frontend/src')

const issues = []
const warnings = []

// Event handler patterns to check
const EVENT_PATTERNS = {
  onClick: {
    pattern: /onClick\s*=\s*\{([^}]+)\}/g,
    validate: (match, content) => {
      // Check if handler is defined
      if (match.includes('undefined') || match.includes('null')) {
        return { error: 'onClick handler is undefined or null' }
      }
      // Check for empty handlers
      if (match.match(/onClick\s*=\s*\{\s*\(\)\s*=>\s*\{\s*\}\s*\}/)) {
        return { warning: 'Empty onClick handler' }
      }
      return null
    }
  },
  onSubmit: {
    pattern: /onSubmit\s*=\s*\{([^}]+)\}/g,
    validate: (match) => {
      // Check for preventDefault
      if (!match.includes('preventDefault')) {
        return { warning: 'onSubmit may need preventDefault()' }
      }
      return null
    }
  },
  onChange: {
    pattern: /onChange\s*=\s*\{([^}]+)\}/g,
    validate: (match) => {
      if (match.includes('undefined')) {
        return { error: 'onChange handler is undefined' }
      }
      return null
    }
  }
}

// Button validation patterns
const BUTTON_PATTERNS = {
  // Buttons should have type attribute
  missingType: {
    pattern: /<button(?![^>]*type=)[^>]*>/gi,
    message: 'Button missing type attribute (should be "button" or "submit")',
    severity: 'warning'
  },
  // Buttons should have onClick or type="submit"
  noHandler: {
    pattern: /<button[^>]*>(?![^<]*onClick)[^<]*<\/button>/gi,
    validate: (match) => {
      if (!match.includes('type="submit"') && !match.includes('onClick')) {
        return { warning: 'Button has no onClick handler and is not type="submit"' }
      }
      return null
    }
  }
}

// Accessibility patterns
const A11Y_PATTERNS = {
  // Images should have alt text
  imgNoAlt: {
    pattern: /<img(?![^>]*alt=)[^>]*>/gi,
    message: 'Image missing alt attribute',
    severity: 'warning'
  },
  // Clickable divs should have role and keyboard handler
  clickableDiv: {
    pattern: /<div[^>]*onClick[^>]*>/gi,
    validate: (match) => {
      const issues = []
      if (!match.includes('role=')) {
        issues.push('Clickable div missing role attribute')
      }
      if (!match.includes('onKeyDown') && !match.includes('onKeyPress') && !match.includes('onKeyUp')) {
        issues.push('Clickable div missing keyboard handler for accessibility')
      }
      if (!match.includes('tabIndex')) {
        issues.push('Clickable div missing tabIndex for keyboard navigation')
      }
      return issues.length > 0 ? { warning: issues.join('; ') } : null
    }
  }
}

function scanFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8')
  const relativePath = path.relative(process.cwd(), filePath)
  const fileIssues = []

  // Check event handlers
  for (const [name, config] of Object.entries(EVENT_PATTERNS)) {
    const matches = content.matchAll(config.pattern)
    for (const match of matches) {
      const result = config.validate(match[0], content)
      if (result) {
        fileIssues.push({
          file: relativePath,
          handler: name,
          ...result,
          line: getLineNumber(content, match.index)
        })
      }
    }
  }

  // Check button patterns
  for (const [name, config] of Object.entries(BUTTON_PATTERNS)) {
    const matches = content.matchAll(config.pattern)
    for (const match of matches) {
      if (config.validate) {
        const result = config.validate(match[0])
        if (result) {
          fileIssues.push({
            file: relativePath,
            check: name,
            ...result,
            line: getLineNumber(content, match.index)
          })
        }
      } else {
        fileIssues.push({
          file: relativePath,
          check: name,
          [config.severity]: config.message,
          line: getLineNumber(content, match.index)
        })
      }
    }
  }

  // Check accessibility patterns
  for (const [name, config] of Object.entries(A11Y_PATTERNS)) {
    const matches = content.matchAll(config.pattern)
    for (const match of matches) {
      if (config.validate) {
        const result = config.validate(match[0])
        if (result) {
          fileIssues.push({
            file: relativePath,
            check: name,
            ...result,
            line: getLineNumber(content, match.index)
          })
        }
      } else {
        fileIssues.push({
          file: relativePath,
          check: name,
          [config.severity]: config.message,
          line: getLineNumber(content, match.index)
        })
      }
    }
  }

  // Check for common React event handling issues
  
  // 1. Check for stopPropagation usage (often needed for nested clickables)
  const nestedClickables = content.match(/<[^>]+onClick[^>]+>[^<]*<[^>]+onClick/g)
  if (nestedClickables) {
    const hasStopPropagation = content.includes('stopPropagation')
    if (!hasStopPropagation) {
      fileIssues.push({
        file: relativePath,
        check: 'nestedClickables',
        warning: 'Nested onClick handlers detected - consider using stopPropagation()',
        line: 0
      })
    }
  }

  // 2. Check for async handlers without error handling
  const asyncHandlers = content.matchAll(/on\w+\s*=\s*\{\s*async\s*\([^)]*\)\s*=>\s*\{(?![^}]*try)/g)
  for (const match of asyncHandlers) {
    fileIssues.push({
      file: relativePath,
      check: 'asyncHandler',
      warning: 'Async event handler without try/catch',
      line: getLineNumber(content, match.index)
    })
  }

  return fileIssues
}

function getLineNumber(content, index) {
  const lines = content.substring(0, index).split('\n')
  return lines.length
}

function scanDirectory(dir) {
  const results = []
  
  if (!fs.existsSync(dir)) {
    console.error(`Directory not found: ${dir}`)
    return results
  }

  const files = fs.readdirSync(dir)
  
  for (const file of files) {
    const filePath = path.join(dir, file)
    const stat = fs.statSync(filePath)
    
    if (stat.isDirectory()) {
      if (!['node_modules', 'dist', 'build', '.git'].includes(file)) {
        results.push(...scanDirectory(filePath))
      }
    } else if (/\.(jsx?|tsx?)$/.test(file)) {
      results.push(...scanFile(filePath))
    }
  }
  
  return results
}

// Main execution
console.log('')
console.log('========================================')
console.log(' Event Handler Audit System')
console.log('========================================')
console.log('')
console.log(`Scanning: ${FRONTEND_PATH}`)
console.log('')

const results = scanDirectory(FRONTEND_PATH)

const errors = results.filter(r => r.error)
const warns = results.filter(r => r.warning)

if (results.length === 0) {
  console.log('\x1b[32m[OK] No event handling issues found!\x1b[0m')
} else {
  console.log(`Found ${results.length} issue(s):`)
  console.log(`  - Errors:   ${errors.length}`)
  console.log(`  - Warnings: ${warns.length}`)
  console.log('')

  // Group by file
  const byFile = {}
  for (const result of results) {
    if (!byFile[result.file]) byFile[result.file] = []
    byFile[result.file].push(result)
  }

  for (const [file, fileResults] of Object.entries(byFile)) {
    console.log(`  ${file}`)
    for (const result of fileResults) {
      const severity = result.error ? '\x1b[31m[ERROR]\x1b[0m' : '\x1b[33m[WARN]\x1b[0m'
      const message = result.error || result.warning
      const line = result.line ? `:${result.line}` : ''
      console.log(`    ${severity} ${message}${line}`)
    }
  }
}

console.log('')
console.log('========================================')

// Exit with error code if errors found
process.exit(errors.length > 0 ? 1 : 0)
