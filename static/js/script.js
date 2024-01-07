let date = new Date();
let year = date.getFullYear();
let month = date.getMonth();
let day = date.getDate();
let minOne = new Date(year, month, day - 1);
let maxDate;
let locations = {}


$(document).ready(function () {
  M.AutoInit();

  $(".sidenav").sidenav({ edge: "right" });

  $(".dropdown-trigger").dropdown();

  $("select").formSelect();

  $(".collapsible").collapsible();

  $(".datepicker").datepicker({
    format: "dd mmmm yyyy",
    yearRange: 1,
    maxDate: minOne,
    showClearBtn: true,
    autoClose: true,
  });

  $(".timepicker").timepicker({
    showClearBtn: true,
    autoClose: true,
  });

  $(".modal").modal();

  // Fetch location data for location autocomplete
  fetch("../static/js/locations.json")
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error("Failed to retrieve autocomplete data");
      }
    })
    .then((locations) => {
      let autoCompleteData = {};
      for (let location of locations) {
        for (let key in location) {
          autoCompleteData[key] = null;
        }
      }
      $("input.autocompletelocation").autocomplete({
        data: autoCompleteData,
      });
    })
    .catch((error) => {
      console.error("Error fetching autocomplete data:", error);
    });

  // Fetch location data for birds autocomplete
  fetch("../static/js/birds.json")
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error("Failed to retrieve autocomplete data");
      }
    })
    .then((birds) => {
      let autoCompleteBirds = {};
      for (let bird of birds) {
        for (let key in bird) {
          autoCompleteBirds[key] = null;
        }
      }
      $("input.autocompletebird").autocomplete({
        data: autoCompleteBirds,
      });
    })
    .catch((error) => {
      console.error("Error fetching autocomplete data:", error);
    });
});


const visibilitySwitch = document.getElementById("visibility-switch");

visibilitySwitch.addEventListener("change", function () {
  document.getElementById("visibility-form").submit();
});

const anonymousSwitch = document.getElementById("anonymous-switch");

anonymousSwitch.addEventListener("change", function () {
  document.getElementById("anonymous-form").submit();
});