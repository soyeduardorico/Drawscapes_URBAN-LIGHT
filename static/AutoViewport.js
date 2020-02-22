// This bit generates auto fit to screen width in smart devices
// See code below for auto fit in smart devices
// https://stackoverflow.com/questions/21419404/setting-the-viewport-to-scale-to-fit-both-width-and-height

function AutoViewport() {}

AutoViewport.setDimensions = function(requiredWidth, requiredHeight) {

/* Conditionally adds a default viewport tag if it does not already exist. */
var insertViewport = function () {

  // do not create if viewport tag already exists
  if (document.querySelector('meta[name="viewport"]'))
    return;

  var viewPortTag=document.createElement('meta');
  viewPortTag.id="viewport";
  viewPortTag.name = "viewport";
  viewPortTag.content = "width=max-device-width, height=max-device-height,initial-scale=1.0";
  document.getElementsByTagName('head')[0].appendChild(viewPortTag);
};

var isPortraitOrientation = function() {
  switch(window.orientation) {  
  case -90:
  case 90:
  return false;
  }

  return true;
 };

var getDisplayWidth = function() {
  if (/iPhone|iPad|iPod/i.test(navigator.userAgent)) {
    if (isPortraitOrientation())
      return screen.width;
    else
      return screen.height;
  }

  return screen.width;
}

var getDisplayHeight = function() {
  if (/iPhone|iPad|iPod/i.test(navigator.userAgent)) {
    if (isPortraitOrientation())
      return screen.height;
    else
      return screen.width;
  }

  // I subtract 180 here to compensate for the address bar.  This is imperfect, but seems to work for my Android tablet using Chrome.
  return screen.height - 180;
}

var adjustViewport = function(requiredWidth, requiredHeight) {

  if (/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent)){

    var actual_height = getDisplayHeight();
    var actual_width = getDisplayWidth();

    var min_width = requiredWidth;
    var min_height = requiredHeight;

    var ratio = Math.min(actual_width / min_width, actual_height / min_height);

    document.querySelector('meta[name="viewport"]').setAttribute('content', 'initial-scale=' + ratio + ', maximum-scale=' + ratio + ', minimum-scale=' + ratio + ', user-scalable=yes, width=' + actual_width);
}    
};

  insertViewport();
  adjustViewport(requiredWidth, requiredHeight);
  window.addEventListener('orientationchange', function() {
    adjustViewport(requiredWidth, requiredHeight);      
  });
};