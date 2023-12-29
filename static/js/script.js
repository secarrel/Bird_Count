let date = new Date();
let year = date.getFullYear();
let month = date.getMonth();
let day = date.getDate();
let minOne = new Date(year, month, day - 1);
let maxDate;

$(document).ready(function () {
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
});
