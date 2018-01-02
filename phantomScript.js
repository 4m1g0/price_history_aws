var page = require('webpage').create(),
  system = require('system'),
  t, address;

if (system.args.length < 3) {
  console.log('Usage: graphs.js <html path> <dest image path>');
  phantom.exit();
}


page.open(system.args[1], function(status) {
  console.log("Status: " + status);
  if(status === "success") {
    window.setTimeout(function () {
            page.render(system.args[2]);
            phantom.exit();
    }, 200)
  } else {
    phantom.exit();
  }
});
