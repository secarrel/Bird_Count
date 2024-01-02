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
      $("input.autocomplete").autocomplete({
        data: autoCompleteData,
      });
    })
    .catch((error) => {
      console.error("Error fetching autocomplete data:", error);
    });
});


