# Scroll Position Fix for MkDocs

This document explains the implementation of the scroll position fix for the MkDocs-based documentation site (docs.neuroca.dev).

## Problem Description

Users reported an issue where the documentation page would automatically scroll back to the top while they were reading content. This made it difficult to read through documentation pages, especially those with complex diagrams or lengthy content.

The problem was caused by a combination of factors:

1. MkDocs Material theme's navigation features (`navigation.instant` and `navigation.tracking`)
2. Dynamic content rendering, particularly Mermaid diagrams and MathJax equations
3. Layout shifts occurring during page load and diagram rendering

## Solution Implementation

The solution is implemented in the custom JavaScript file `assets/js/fix-scroll.js` which preserves scroll position and prevents unwanted scroll resets.

### Key Components of the Solution

1. **Scroll Position Tracking**:
   - Listens for scroll events and stores the user's current scroll position
   - Detects when scroll position changes unexpectedly (e.g., jumps back to top)
   - Restores the previous scroll position when unwanted jumps are detected

2. **Layout Shift Handling**:
   - Uses MutationObserver to detect DOM changes that might cause layout shifts
   - Applies scroll position restoration when layout shifts affect scroll position
   - Includes a counter mechanism to prevent infinite restoration loops

3. **Mermaid Integration**:
   - Specifically targets Mermaid diagram rendering events
   - Captures scroll position before Mermaid diagrams render
   - Restores position after rendering completes

4. **Navigation Feature Compatibility**:
   - Works alongside Material theme's navigation features
   - Ensures back-to-top button still functions as expected
   - Handles page transitions smoothly

### Technical Implementation Details

The script uses the following techniques to achieve smooth scrolling behavior:

- Uses passive event listeners for scroll events to maintain performance
- Employs timeouts to distinguish between user-initiated scrolling and unwanted jumps
- Tracks scroll state with flags to prevent recursive scroll operations
- Modifies certain MkDocs features' behavior without disabling their functionality

## Future Maintenance

If updating the MkDocs Material theme or changing navigation features, consider the following:

1. Review the `navigation` features enabled in `mkdocs.yml`
2. Test scrolling behavior after any theme updates
3. Check mermaid diagram rendering if diagram syntax or the mermaid version is updated

## Alternative Solutions Considered

Other approaches that were considered but not implemented:

1. **Disabling Navigation Features**: Could have disabled `navigation.instant` and `navigation.tracking`, but this would sacrifice useful functionality.
2. **Static Pre-rendering of Diagrams**: Pre-rendering Mermaid diagrams as static images would prevent layout shifts but reduce diagram quality and interactivity.
3. **CSS-only Fix**: Attempted to use CSS to fix the issue, but JavaScript was necessary to actively monitor and correct scroll position.

## Related Files

- `docs/pages/assets/js/fix-scroll.js` - The JavaScript implementation
- `docs/mkdocs.yml` - Configuration file where the script is included
