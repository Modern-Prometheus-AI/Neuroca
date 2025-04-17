/**
 * Scroll position fix for docs.neuroca.dev
 * 
 * This script fixes the issue where the page jumps back to the top when scrolling.
 * It works by:
 * 1. Storing scroll position
 * 2. Detecting when layout shifts occur from diagrams or dynamic content loading
 * 3. Restoring the scroll position after content stabilizes
 */

(function() {
  // Variables to track scroll position and state
  let lastScrollPosition = 0;
  let scrollResetTimeout = null;
  let isManuallyScrolling = false;
  let scrollStabilityCounter = 0;
  
  // Store scroll position when the user scrolls
  document.addEventListener('scroll', function(e) {
    if (!isManuallyScrolling) {
      lastScrollPosition = window.scrollY;
      
      // Clear any existing timeout
      if (scrollResetTimeout) {
        clearTimeout(scrollResetTimeout);
      }
      
      // Set a timeout to check if scroll position changes unexpectedly
      scrollResetTimeout = setTimeout(checkScrollPosition, 100);
    }
  }, { passive: true });
  
  // Check if scroll position was reset unexpectedly
  function checkScrollPosition() {
    // If current scroll position is significantly different from stored position
    // and we're not at the top or bottom of the page by user action
    if (Math.abs(window.scrollY - lastScrollPosition) > 50 && window.scrollY < lastScrollPosition) {
      // Restore the saved scroll position
      restoreScrollPosition();
    }
  }
  
  // Restore scroll position
  function restoreScrollPosition() {
    isManuallyScrolling = true;
    
    // Smoothly scroll back to the last known position
    window.scrollTo({
      top: lastScrollPosition,
      behavior: 'auto' // Use 'auto' instead of 'smooth' to prevent visual jumping
    });
    
    // Reset the flag after a short delay
    setTimeout(function() {
      isManuallyScrolling = false;
    }, 50);
  }
  
  // Additional handler for layout shifts that may occur after page load
  // Particularly for Mermaid diagrams and MathJax elements
  if (window.MutationObserver) {
    // Watch for DOM changes that might cause layout shifts
    const observer = new MutationObserver(function(mutations) {
      for (const mutation of mutations) {
        if (mutation.type === 'childList' || mutation.type === 'attributes') {
          // Only restore if we've detected a potential layout shift and we're not at the top
          if (window.scrollY < lastScrollPosition && window.scrollY > 0 && lastScrollPosition > 100) {
            // Use a counter to ensure we only attempt to restore position a reasonable number of times
            if (scrollStabilityCounter < 5) {
              scrollStabilityCounter++;
              restoreScrollPosition();
            }
          }
        }
      }
    });
    
    // Start observing the document body for changes
    observer.observe(document.body, { 
      childList: true, 
      subtree: true,
      attributes: true,
      attributeFilter: ['style', 'class']
    });
    
    // Reset counter periodically
    setInterval(function() {
      scrollStabilityCounter = 0;
    }, 5000);
  }
  
  // For Mermaid diagrams specifically
  if (window.mermaid) {
    const originalInit = window.mermaid.initialize;
    
    // Override mermaid initialize to capture scroll position before rendering
    window.mermaid.initialize = function(config) {
      lastScrollPosition = window.scrollY;
      const result = originalInit.call(this, config);
      
      // After mermaid init, we need to wait for rendering to complete
      setTimeout(function() {
        // Check if scroll position was reset by mermaid rendering
        if (window.scrollY < lastScrollPosition && lastScrollPosition > 100) {
          restoreScrollPosition();
        }
      }, 300);
      
      return result;
    };
  }
  
  // Handle any potential issues with navigation.instant feature
  document.addEventListener('DOMContentLoaded', function() {
    // Store initial scroll position after page load
    setTimeout(function() {
      lastScrollPosition = window.scrollY;
    }, 500);
  });
  
  // Disable navigation.top button automatic triggering if present
  // This targets Material theme's back-to-top button
  setTimeout(function() {
    const backToTopButton = document.querySelector('.md-top');
    if (backToTopButton) {
      // Ensure it only activates on click, not on scroll events
      backToTopButton.addEventListener('click', function(e) {
        // Allow this click to proceed normally
        lastScrollPosition = 0; // Update our tracking
      });
    }
  }, 1000);
})();
