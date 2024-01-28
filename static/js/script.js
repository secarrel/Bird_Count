let date = new Date();
let year = date.getFullYear();
let month = date.getMonth();
let day = date.getDate();
let minOne = new Date(year, month, day);
let maxDate;
let locations = {}

// -------------- Execute when page is ready ---------------
$(document).ready(function () {
  // Automatically initialise materialize
  M.AutoInit();

  // Activate sidebar navigation for mobile view
  $(".sidenav").sidenav({ edge: "right" });

  // Activate dropdown for navbar
  $(".dropdown-trigger").dropdown();

  // Activate the dropdown select input for experience field
  $("select").formSelect();

  // Activate the collapsible messages board
  $(".collapsible").collapsible();

  // Activate tooltips
  $(".tooltipped").tooltip();

  // Activate the date picker for adding observations
  $(".datepicker").datepicker({
    format: "dd mmmm yyyy",
    yearRange: 1,
    maxDate: minOne,
    showClearBtn: true,
    autoClose: true,
    defaultDate: date,
  });

  // Activate the timepicker for adding observations
  $(".timepicker").timepicker({
    showClearBtn: true,
    autoClose: true,
  });

  // Activate modals
  $(".modal").modal();

  // Fetch location data for location autocomplete
  fetch("../static/js/locations.json")
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error("Failed to retrieve location data");
      }
    })
    .then((locations) => {
      let autoCompleteData = {};
      for (let location of locations) {
        for (let key in location) {
          autoCompleteData[key] = null;
        }
      }
      // Activate autocomplete
      $("input.autocompleteLocation").autocomplete({
        data: autoCompleteData,
      });
    })
    .catch((error) => {
      console.error("Error fetching location data:", error);
    });

  // Fetch bird data for birds autocomplete
  fetch("../static/js/birds.json")
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error("Failed to retrieve bird data");
      }
    })
    .then((birds) => {
      let autoCompleteBirds = {};
      for (let bird of birds) {
        for (let key in bird) {
          autoCompleteBirds[key] = null;
        }
      }
      // Activate autocomplete
      $("input.autocompleteBird").autocomplete({
        data: autoCompleteBirds,
      });
    })
    .catch((error) => {
      console.error("Error fetching bird data:", error);
    });
});

// -------------- Privacy switches ---------------
// Identify switch elements
const visibilitySwitch = document.getElementById("visibility-switch");
const anonymousSwitch = document.getElementById("anonymous-switch");
const visibilityForm = document.getElementById("visibility-form");
const anonymousForm = document.getElementById("anonymous-form");

// Add event listener to visibility switch so it's value is submitted on change
if (visibilitySwitch && visibilityForm) {
  visibilitySwitch.addEventListener("change", function () {
    document.getElementById("visibility-form").submit();
  });
}

// Add event listener to anonymity switch so it's value is submitted on change
if (anonymousSwitch && anonymousForm) {
  anonymousSwitch.addEventListener("change", function () {
    document.getElementById("anonymous-form").submit();
  });
}

// -------------- Redirect User ---------------
document.addEventListener("DOMContentLoaded", function () {
  // Check if the target element exists
  let redirectAddObs = document.getElementById("redirect-add-obs");

  if (redirectAddObs) {
    // The target element has loaded
    // Redirect the user to a new page
    window.location.href = "/login/";
  }
});


// -------------- Fill and open observation modal ---------------
let observationRow = document.querySelectorAll(".observation-modal-trigger");
let observationModal = document.getElementById("observation-details")

observationRow.forEach(function(observation) {
  observation.addEventListener("click", function () {
    let species = observation.dataset.species;
    let location = observation.dataset.location;
    let date = observation.dataset.date;
    let time = observation.dataset.time;
    let seenBy = observation.dataset.seenBy;
    let quantity = observation.dataset.quantity;
    let observationId = observation.dataset.id;
    let anonymous = observation.dataset.anonymous;
    let certainty = observation.dataset.certainty;

    if (anonymous === "True") {
      seenBy = "AnonymousBirdy";
    }
    
  // Get image for this observation
  fetch(`/get_image/${observationId}`)
    .then((response) => response.blob())
    .then((image) => {
      let imageUrl = URL.createObjectURL(image);
      let modalImage = document.getElementById("observation-image");
    
      // When image has loaded, change modal content and open.
      modalImage.onload = function() {
        document.getElementById("observation-title").innerText =
          species + " by " + seenBy;
        document.getElementById("observation-location").innerText =
          "Location: " + location;
        document.getElementById("observation-date").innerText =
          "Seen: " + date + " @ " + time;
        document.getElementById("observation-quantity").innerText =
          "Quantity: " + quantity;
        document.getElementById("observation-certainty").innerText =
          "Certainty: " + certainty + "/10";

        // Open the modal
        let instance = M.Modal.getInstance(observationModal);
        instance.open();
      };

      modalImage.src = imageUrl;
    
    });
  });
});
